import importlib
import json
import logging
import random
import time
import uuid

from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Any, Callable, Generator, Literal, Optional, Union
from uuid import uuid4

import arrow
import pytest
import yaml

from azure.storage.blob import BlobClient
from pytest_bdd import given, parsers, then, when
from sqlalchemy import create_engine, update
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import create_database, database_exists, drop_database

import settings

from azure_actions.blob_storage import put_new_reward_updates_file
from db.carina import models as carina_models
from db.carina.models import FetchType, Retailer, RetailerFetchType, Reward, RewardConfig
from db.hubble import models as hubble_models
from db.polaris import models as polaris_models
from db.polaris.models import AccountHolder, AccountHolderCampaignBalance
from db.vela import models as vela_models
from db.vela.models import Campaign, EarnRule, RetailerRewards, RewardRule
from settings import (
    BLOB_STORAGE_DSN,
    CARINA_DATABASE_URI,
    CARINA_TEMPLATE_DB_NAME,
    HUBBLE_DATABASE_URI,
    HUBBLE_TEMPLATE_DB_NAME,
    POLARIS_DATABASE_URI,
    POLARIS_TEMPLATE_DB_NAME,
    SQL_DEBUG,
    VELA_DATABASE_URI,
    VELA_TEMPLATE_DB_NAME,
)
from tests.api.base import Endpoints
from tests.db_actions.carina import get_fetch_type_id, get_retailer_id, get_reward_config_id
from tests.db_actions.polaris import (
    create_pending_rewards_for_existing_account_holder,
    create_rewards_for_existing_account_holder,
    get_account_holder_for_retailer,
)

from tests.db_actions.retry_tasks import RetryTaskStatuses, get_latest_task
from tests.db_actions.vela import get_campaign_by_slug
from tests.requests.enrolment import send_get_accounts
from tests.requests.transaction import post_transaction_request
from tests.shared_utils.fixture_loader import load_fixture
from tests.shared_utils.redis import pause_redis, unpause_redis

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from sqlalchemy.orm import Session

    from db.polaris.models import RetailerConfig

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def polaris_db_session() -> Generator:
    if database_exists(POLARIS_DATABASE_URI):
        logger.info("Dropping Polaris database")
        drop_database(POLARIS_DATABASE_URI)
    logger.info("Creating Polaris database")
    create_database(POLARIS_DATABASE_URI, template=POLARIS_TEMPLATE_DB_NAME)
    engine = create_engine(POLARIS_DATABASE_URI, poolclass=NullPool, echo=SQL_DEBUG)
    polaris_models.Base.prepare(autoload_with=engine)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session
    importlib.reload(polaris_models)


@pytest.fixture(autouse=True)
def vela_db_session() -> Generator:
    if database_exists(VELA_DATABASE_URI):
        logger.info("Dropping Vela database")
        drop_database(VELA_DATABASE_URI)
    logger.info("Creating Vela database")
    create_database(VELA_DATABASE_URI, template=VELA_TEMPLATE_DB_NAME)
    engine = create_engine(VELA_DATABASE_URI, poolclass=NullPool, echo=SQL_DEBUG)
    vela_models.Base.prepare(autoload_with=engine)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session
    importlib.reload(vela_models)


@pytest.fixture(autouse=True)
def carina_db_session() -> Generator:
    if database_exists(CARINA_DATABASE_URI):
        logger.info("Dropping Carina database")
        drop_database(CARINA_DATABASE_URI)
    logger.info("Creating Carina database")
    create_database(CARINA_DATABASE_URI, template=CARINA_TEMPLATE_DB_NAME)
    engine = create_engine(CARINA_DATABASE_URI, poolclass=NullPool, echo=SQL_DEBUG)
    carina_models.Base.prepare(autoload_with=engine)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session
    importlib.reload(carina_models)


@pytest.fixture(autouse=True)
def hubble_db_session() -> Generator:
    if database_exists(HUBBLE_DATABASE_URI):
        logger.info("Dropping Hubble database")
        drop_database(HUBBLE_DATABASE_URI)
    logger.info("Creating Hubble database")
    create_database(HUBBLE_DATABASE_URI, template=HUBBLE_TEMPLATE_DB_NAME)
    engine = create_engine(HUBBLE_DATABASE_URI, poolclass=NullPool, echo=SQL_DEBUG)
    hubble_models.Base.prepare(autoload_with=engine)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session
    importlib.reload(hubble_models)


# This is the only way I could get the cucumber plugin to work
# in vscode with target_fixture and play nice with flake8
# https://github.com/alexkrechik/VSCucumberAutoComplete/issues/373
# fmt: off
@given(parsers.parse("the {retailer_slug} retailer exists"),
       target_fixture="retailer_config",
       )
# fmt: on
def retailer(
    polaris_db_session: "Session",
    vela_db_session: "Session",
    carina_db_session: "Session",
    retailer_slug: str,
    request_context: dict,
) -> polaris_models.RetailerConfig:
    fixture_data = load_fixture(retailer_slug)
    retailer_config = polaris_models.RetailerConfig(**fixture_data.retailer_config)
    polaris_db_session.add(retailer_config)
    retailer_rewards = RetailerRewards(slug=retailer_slug)
    vela_db_session.add(retailer_rewards)
    retailer = Retailer(slug=retailer_slug)
    carina_db_session.add(retailer)
    polaris_db_session.commit()
    vela_db_session.commit()
    carina_db_session.commit()
    logging.info(retailer_config)
    request_context["carina_retailer_id"] = retailer.id
    return retailer_config


@when(parsers.parse("the task worker queue is full"))
def stop_redis() -> None:
    pause_redis(seconds=10)


@when(parsers.parse("the task worker queue is ready"))
def resume_redis() -> None:
    unpause_redis()


# fmt: off
@given(parsers.parse("that retailer has the standard campaigns configured"),
       target_fixture="standard_campaigns",
       )
# fmt: on
def standard_campaigns_and_reward_slugs(
    campaign_slug: str, vela_db_session: "Session", retailer_config: "RetailerConfig"
) -> list[Campaign]:
    fixture_data = load_fixture(retailer_config.slug)
    campaigns: list = []

    for campaign_data in fixture_data.campaign:
        campaign = Campaign(retailer_id=retailer_config.id, **campaign_data)
        vela_db_session.add(campaign)
        vela_db_session.flush()
        campaigns.append(campaign)

        vela_db_session.add_all(
            EarnRule(campaign_id=campaign.id, **earn_rule_data)
            for earn_rule_data in fixture_data.earn_rule.get(campaign.slug, [])
        )

        vela_db_session.add_all(
            RewardRule(campaign_id=campaign.id, **reward_rule_data)
            for reward_rule_data in fixture_data.reward_rule.get(campaign.slug, [])
        )

    vela_db_session.commit()
    return campaigns


# fmt: off
@given(parsers.parse("the retailer's {campaign_slug} {loyalty_type} campaign starts {starts_when} "
                     "and ends {ends_when} and is {status}"))
# fmt: on
def create_campaign(
    campaign_slug: str,
    loyalty_type: Union[Literal["STAMPS"], Literal["ACCUMULATOR"]],
    starts_when: str,
    ends_when: str,
    status: str,
    vela_db_session: "Session",
    retailer_config: "RetailerConfig",
) -> None:

    arw = arrow.utcnow()
    start_date = arw.dehumanize(starts_when).date()
    end_date = arw.dehumanize(ends_when).date()
    campaign = Campaign(
        retailer_id=retailer_config.id,
        slug=campaign_slug,
        name=campaign_slug,
        loyalty_type=loyalty_type,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )
    vela_db_session.add(campaign)
    vela_db_session.commit()


# fmt: off
@given(parsers.parse("the {campaign_slug} campaign has an "
                     "earn rule with a threshold of {threshold}, an increment of {inc} and "
                     "a multiplier of {mult}"))
# fmt: on
def create_stamps_earn_rule(
    vela_db_session: "Session",
    campaign_slug: str,
    threshold: int,
    inc: int,
    mult: int,
) -> None:
    campaign = vela_db_session.execute(select(Campaign).where(Campaign.slug == campaign_slug)).scalar_one()
    earn_rule = EarnRule(
        campaign_id=campaign.id, threshold=threshold, increment=inc, increment_multiplier=mult, max_amount=None
    )

    vela_db_session.add(earn_rule)
    vela_db_session.commit()


# fmt: off
@given(parsers.parse("the {campaign_slug} campaign has an earn rule with a threshold of {threshold}, "
                     "an increment of {inc}, a multiplier of {mult} and max amount of {earn_max_amount}"))
# fmt: on
def create_accumulator_earn_rule(
    vela_db_session: "Session",
    campaign_slug: str,
    threshold: int,
    inc: int,
    mult: int,
    earn_max_amount: int,
) -> None:
    campaign = vela_db_session.execute(select(Campaign).where(Campaign.slug == campaign_slug)).scalar_one()
    earn_rule = EarnRule(
        campaign_id=campaign.id,
        threshold=threshold,
        increment=inc,
        increment_multiplier=mult,
        max_amount=earn_max_amount,
    )

    vela_db_session.add(earn_rule)
    vela_db_session.commit()


# fmt: off
@given(parsers.parse("the {campaign_slug} campaign has reward rule of {reward_rule}, with reward slug {reward_slug} "
                     "and allocation window {allocation_window}"))
# fmt: on
def create_reward_rule(
    campaign_slug: str, reward_rule: int, reward_slug: str, allocation_window: int, vela_db_session: "Session"
) -> None:
    campaign = get_campaign_by_slug(vela_db_session=vela_db_session, campaign_slug=campaign_slug)
    # earn_rule = EarnRule(campaign_id=campaign.id, threshold=threshold, increment=inc, increment_multiplier=mult)
    reward_rule = RewardRule(
        campaign_id=campaign.id, reward_goal=reward_rule, reward_slug=reward_slug, allocation_window=allocation_window
    )
    vela_db_session.add(reward_rule)
    vela_db_session.commit()


# fmt: off
@given(parsers.parse("the retailer has a {reward_slug} reward config configured with {required_fields_values}, "
                     "and a status of {status} and a {fetch_type_name} fetch type"))
# fmt: on
def add_reward_config(
    carina_db_session: "Session",
    reward_slug: str,
    required_fields_values: str,
    status: str,
    retailer_config: "RetailerConfig",
    fetch_type_name: str,
) -> None:
    retailer_id = get_retailer_id(carina_db_session=carina_db_session, retailer_slug=retailer_config.slug)
    fetch_type_id = get_fetch_type_id(carina_db_session=carina_db_session, fetch_type_name=fetch_type_name)
    reward_config = RewardConfig(
        reward_slug=reward_slug,
        retailer_id=retailer_id,
        status=status,
        required_fields_values=required_fields_values,
        fetch_type_id=fetch_type_id,
    )
    carina_db_session.add(reward_config)
    carina_db_session.commit()


# fmt: off
@given(parsers.parse("a {fetch_type_name} fetch type is configured for the current retailer "
                     "with an agent config brand id {brand_id:d}"))
# fmt: on
def add_retailer_fetch_type_egift(
    carina_db_session: "Session",
    retailer_config: "RetailerConfig",
    fetch_type_name: str,
    brand_id: int,
) -> None:

    agent_config = {"base_url": settings.API_REFLECTOR_BASE_URL, "brand_id": brand_id}

    retailer_fetch_type = RetailerFetchType(
        retailer_id=get_retailer_id(carina_db_session=carina_db_session, retailer_slug=retailer_config.slug),
        fetch_type_id=get_fetch_type_id(carina_db_session=carina_db_session, fetch_type_name=fetch_type_name),
        agent_config=yaml.dump(agent_config),
    )
    carina_db_session.add(retailer_fetch_type)
    carina_db_session.commit()


# fmt: off
@given(parsers.parse("a {fetch_type_name} fetch type is configured for the current retailer with "
                     "an agent config of {agent_config}"))
# fmt: on
def add_retailer_fetch_type_preloaded(
    carina_db_session: "Session",
    retailer_config: "RetailerConfig",
    fetch_type_name: str,
    agent_config: Optional[str],
) -> None:

    retailer_fetch_type = RetailerFetchType(
        retailer_id=get_retailer_id(carina_db_session=carina_db_session, retailer_slug=retailer_config.slug),
        fetch_type_id=get_fetch_type_id(carina_db_session=carina_db_session, fetch_type_name=fetch_type_name),
        agent_config=None,
    )
    carina_db_session.add(retailer_fetch_type)
    carina_db_session.commit()


# fmt: off
@when(parsers.parse("{rewards_n:d} rewards are generated for the {reward_slug} reward config with allocation status "
                    "set to {allocation_status} and deleted status set to {deleted_status}"),
      target_fixture="available_rewards")
@given(parsers.parse(
    "there is {rewards_n:d} reward configured for the {reward_slug} reward config, with allocation status set to "
    "{allocation_status} and deleted status set to {deleted_status}"),
    target_fixture="available_rewards")
# fmt: on
def add_rewards(
    carina_db_session: "Session",
    reward_slug: str,
    allocation_status: str,
    deleted_status: str,
    retailer_config: "RetailerConfig",
    rewards_n: int,
) -> list[Reward]:
    allocation_status_bool = allocation_status == "true"
    deleted_status_bool = deleted_status == "true"
    reward_config_id = get_reward_config_id(carina_db_session=carina_db_session, reward_slug=reward_slug)
    rewards: list[Reward] = []

    if rewards_n > 0:
        for i in range(rewards_n):
            reward = Reward(
                id=str(uuid4()),
                code=f"{reward_slug}/{i}",
                allocated=allocation_status_bool,
                deleted=deleted_status_bool,
                reward_config_id=reward_config_id,
                retailer_id=retailer_config.id,
            )
            carina_db_session.add(reward)
            carina_db_session.commit()
            rewards.append(reward)

    return rewards


# fmt: off
@given(parsers.parse("that campaign has the standard reward config configured with {reward_n:d} allocable rewards"),
       target_fixture="standard_reward_configs",
       )
# fmt: on
def standard_reward_and_reward_config(
    carina_db_session: "Session",
    reward_n: int,
    retailer_config: "RetailerConfig",
    request_context: dict,
    fetch_types: list[FetchType],
) -> list[RewardConfig]:
    fixture_data = load_fixture(retailer_config.slug)
    reward_configs: list = []
    for fetch_type in fetch_types:

        for reward_config_data in fixture_data.reward_config.get(fetch_type.name, []):
            reward_config = RewardConfig(
                retailer_id=request_context["carina_retailer_id"], fetch_type_id=fetch_type.id, **reward_config_data
            )
            carina_db_session.add(reward_config)
            reward_configs.append(reward_config)

    if reward_n > 0:
        carina_db_session.flush()
        for config in reward_configs:
            carina_db_session.add_all(
                Reward(
                    id=str(uuid4()),
                    code=f"{config.reward_slug}/{i}",
                    allocated=False,
                    deleted=False,
                    reward_config_id=config.id,
                    retailer_id=request_context["carina_retailer_id"],
                )
                for i in range(1, reward_n + 1)
            )

    carina_db_session.commit()
    return reward_configs


# fmt: off
@given(parsers.parse("required fetch type are configured for the current retailer"),
       target_fixture="fetch_types"
       )
# fmt: on
def get_fetch_type(
    carina_db_session: "Session", retailer_config: "RetailerConfig", request_context: dict
) -> list[FetchType]:
    fixture_data = load_fixture(retailer_config.slug)
    retailer_id = request_context["carina_retailer_id"]
    fetch_types = carina_db_session.execute(select(FetchType)).scalars().all()
    for fetch_type in fetch_types:
        if fetch_type.name in fixture_data.retailer_fetch_type:
            carina_db_session.add(
                RetailerFetchType(
                    retailer_id=retailer_id,
                    fetch_type_id=fetch_type.id,
                    **fixture_data.retailer_fetch_type[fetch_type.name],
                )
            )

    carina_db_session.commit()
    return fetch_types


# Hooks
def pytest_bdd_step_error(
    request: Any,
    feature: Any,
    scenario: Any,
    step: Any,
    step_func: Any,
    step_func_args: Any,
    exception: Any,
) -> None:
    """This function will log the failed BDD-Step at the end of logs"""
    logging.info(f"Step failed: {step}")


def pytest_html_report_title(report: Any) -> None:
    """Customized title for html report"""
    report.title = "BPL QA System Automation Results"


@pytest.fixture(scope="function")
def request_context() -> dict:
    return {}


# @pytest.fixture(scope="session", autouse=True)
# def configure_html_report_env(request: "SubRequest", env: str, channel: str) -> None:
#     """Delete existing data in the test report and add bpl execution details"""
#
#     metadata: dict = getattr(request.config, "_metadata")
#
#     for ele in list(metadata.keys()):
#         del metadata[ele]
#     # if re.search(r'^(GITLAB_|CI_)', k): for git lab related extra table contents
#     metadata.update({"Test Environment": env.upper(), "Channel": channel})


def pytest_addoption(parser: "Parser") -> None:
    parser.addoption("--env", action="store", default="staging", help="env : can be dev or staging or prod")
    parser.addoption("--channel", action="store", default="user-channel", help="env : can be dev or staging or prod")


@pytest.fixture(scope="session")
def env(pytestconfig: "Config") -> Generator:
    """Returns current environment"""
    return pytestconfig.getoption("env")


@pytest.fixture(scope="session")
def channel(pytestconfig: "Config") -> Generator:
    """Returns current environment"""
    return pytestconfig.getoption("channel")


# fmt: off
@given(parsers.parse("an {status} account holder exists for the retailer"),
       target_fixture="account_holder",
       )
# fmt: on
def setup_account_holder(
    status: str,
    retailer_config: "RetailerConfig",
    polaris_db_session: "Session",
    vela_db_session: "Session",
) -> AccountHolder:

    account_status = {"active": "ACTIVE", "pending": "PENDING", "inactive": "INACTIVE"}.get(status, "PENDING")
    fixture_data = load_fixture(retailer_config.slug)
    account_holder = AccountHolder(
        email=f"pytest+{uuid4()}@bink.com",
        status=account_status,
        account_number=fixture_data.retailer_config["account_number_prefix"] + str(random.randint(1, (10**10))),
        retailer_id=retailer_config.id,
        account_holder_uuid=str(uuid4()),
        opt_out_token=str(uuid4()),
    )
    polaris_db_session.add(account_holder)
    polaris_db_session.flush()

    campaigns = (
        vela_db_session.execute(
            select(Campaign).where(Campaign.retailer_id == retailer_config.id, Campaign.status == "ACTIVE")
        )
        .scalars()
        .all()
    )
    for campaign in campaigns:
        balance = AccountHolderCampaignBalance(
            account_holder_id=account_holder.id, campaign_slug=campaign.slug, balance=0
        )
        polaris_db_session.add(balance)

    polaris_db_session.commit()
    return account_holder


# fmt: off
@given(parsers.parse("the account has {reward_count} issued unexpired rewards"))
# fmt: on
def update_existing_account_holder_with_rewards(
    account_holder: AccountHolder,
    retailer_config: "RetailerConfig",
    reward_count: int,
    polaris_db_session: "Session",
) -> AccountHolder:

    create_rewards_for_existing_account_holder(
        polaris_db_session, retailer_config.slug, reward_count, account_holder.id
    )

    return account_holder


# fmt: off
@given(parsers.parse("the account has {count} pending rewards for {campaign_slug} with value {reward_goal}"))
# fmt: on
def update_existing_account_holder_with_pending_rewards(
    account_holder: AccountHolder,
    retailer_config: "RetailerConfig",
    count: int,
    polaris_db_session: "Session",
    reward_goal: int,
    campaign_slug: str,
) -> AccountHolder:

    create_pending_rewards_for_existing_account_holder(
        polaris_db_session, retailer_config.slug, count, account_holder.id, campaign_slug, reward_goal
    )

    return account_holder


@when(parsers.parse("BPL receives a transaction for the account holder for the amount of {amount} pennies"))
def the_account_holder_transaction_request(
    account_holder: AccountHolder, retailer_config: "RetailerConfig", amount: int, request_context: dict
) -> None:

    payload = {
        "id": str(uuid4()),
        "transaction_total": int(amount),
        "datetime": int(datetime.utcnow().timestamp()),
        "MID": "12432432",
        "loyalty_id": str(account_holder.account_holder_uuid),
        "transaction_id": "BPL" + str(random.randint(1, (10**10))),
    }
    logging.info(f"Payload of transaction : {json.dumps(payload)}")
    post_transaction_request(payload, retailer_config.slug, request_context)


# fmt: off
@then(parsers.parse("{expected_num_rewards:d} {state} rewards are available to the account holder"))
# fmt: on
def send_get_request_to_account_holder(
    retailer_config: "RetailerConfig", account_holder: AccountHolder, expected_num_rewards: int, state: str
) -> None:
    time.sleep(3)
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )
    if state == "issued":
        assert len(resp.json()["rewards"]) == expected_num_rewards
        for i in range(expected_num_rewards):
            assert resp.json()["rewards"][i]["code"]
            assert resp.json()["rewards"][i]["issued_date"]
            assert resp.json()["rewards"][i]["redeemed_date"] is None
            assert resp.json()["rewards"][i]["expiry_date"]
            assert resp.json()["rewards"][i]["status"] == state
    elif state == "pending":
        for i in range(expected_num_rewards):
            assert resp.json()["pending_rewards"][i]["created_date"] is not None
            assert resp.json()["pending_rewards"][i]["conversion_date"] is not None


# fmt: off
@given(parsers.parse("the account holder's {campaign_slug} balance is {amount:d}"))
# fmt: on
def update_existing_account_holder_with_campaign_balance(
    account_holder: AccountHolder, amount: int, polaris_db_session: "Session", campaign_slug: str
) -> None:

    polaris_db_session.execute(
        update(AccountHolderCampaignBalance)
        .values(balance=amount)
        .where(
            AccountHolderCampaignBalance.account_holder_id == account_holder.id,
            AccountHolderCampaignBalance.campaign_slug == campaign_slug,
        )
    )

    polaris_db_session.commit()
    logging.info(f"Account holder balance updated to {amount}")


@then(parsers.parse("the account holder's {campaign_slug} balance is returned as {amount:d}"))
def account_holder_balance_correct(
    polaris_db_session: "Session", account_holder: AccountHolder, campaign_slug: str, amount: int
) -> None:
    time.sleep(2)
    polaris_db_session.refresh(account_holder)
    balances_by_slug = {ahcb.campaign_slug: ahcb for ahcb in account_holder.accountholdercampaignbalance_collection}
    for i in range(5):
        sleep(i)
        if balances_by_slug[campaign_slug].balance == amount:
            break
        logging.info(f"Account holder balance is {balances_by_slug[campaign_slug].balance} didnt match")

    assert balances_by_slug[campaign_slug].balance == amount
    logging.info(f"Account holder balance is {balances_by_slug[campaign_slug].balance}")


@then(parsers.parse("the newly enrolled account holder's {campaign_slug} balance is {amount:d}"))
def get_account_and_check_balance(
    polaris_db_session: "Session", campaign_slug: str, amount: int, retailer_config: "RetailerConfig"
) -> None:
    time.sleep(2)
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)
    polaris_db_session.refresh(account_holder)
    balances_by_slug = {ahcb.campaign_slug: ahcb for ahcb in account_holder.accountholdercampaignbalance_collection}
    assert balances_by_slug[campaign_slug].balance == amount


@pytest.fixture(scope="function")
def upload_reward_updates_to_blob_storage() -> Callable:
    def func(
        retailer_slug: str, rewards: list[Reward], reward_status: str, blob_name: str = None
    ) -> Optional[BlobClient]:
        """Upload some reward updates to blob storage to test end-to-end import"""
        blob = None
        if blob_name is None:
            blob_name = f"test_import_{uuid.uuid4()}.csv"

        if BLOB_STORAGE_DSN:
            logger.debug(f"Uploading reward updates to blob storage for {retailer_slug}...")
            blob = put_new_reward_updates_file(
                retailer_slug=retailer_slug, rewards=rewards, blob_name=blob_name, reward_status=reward_status
            )
            logger.debug(f"Successfully uploaded reward updates to blob storage: {blob.url}")
        else:
            logger.debug("No BLOB_STORAGE_DSN set, skipping reward updates upload")

        return blob

    return func


# fmt: off
@then(parsers.parse("{expected_num_rewards:d} reward for the account holder shows as {reward_status} "
                    "with redeemed date"))
# fmt: on
def verify_account_holder_reward_status(
    retailer_config: "RetailerConfig", account_holder: AccountHolder, expected_num_rewards: int, reward_status: str
) -> None:
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )
    assert len(resp.json()["rewards"]) == expected_num_rewards
    for i in range(expected_num_rewards):
        redeemed_date = resp.json()["rewards"][i]["redeemed_date"]
        if reward_status == "redeemed":
            assert redeemed_date is not None
        elif reward_status == "cancelled":
            assert redeemed_date is None
        assert resp.json()["rewards"][i]["status"] == reward_status


# fmt: off
@when(parsers.parse("the {task_name} task status is cancelled"))
# fmt: on
def check_retry_task_status(vela_db_session: "Session", task_name: str) -> None:
    for i in range(5):
        sleep(i)
        status = get_latest_task(vela_db_session, task_name)
        if status[0] == RetryTaskStatuses.CANCELLED:
            break

    assert status[0] == RetryTaskStatuses.CANCELLED


# fmt: off
@when(parsers.parse("the {task_name} task status is {retry_status}"))
# fmt: on
def check_retry_task_status_fail(carina_db_session: "Session", task_name: str, retry_status: str) -> None:
    if retry_status == "failed":
        enum_status = RetryTaskStatuses.FAILED

    for i in range(15):
        sleep(i)
        status = get_latest_task(carina_db_session, task_name)
        if status is not None and status.status == enum_status:
            break

    assert status.status == enum_status


# fmt: off
@given(parsers.parse("there are {reward_count} issued unexpired rewards for account holder with "
                     "reward slug {reward_slug}"))
# fmt: on
def update_existing_account_holder_with_rewards_for_reward_slug(
    account_holder: AccountHolder,
    retailer_config: "RetailerConfig",
    reward_count: int,
    reward_slug: str,
    polaris_db_session: "Session",
) -> AccountHolder:
    create_rewards_for_existing_account_holder(
        polaris_db_session, retailer_config.slug, reward_count, account_holder.id, reward_slug
    )
    return account_holder


# fmt: off
@then(parsers.parse("there is no balance shown for {campaign_slug} for account holder"))
# fmt: on
def send_get_request_to_accounts_check_balance_for_campaign(
    retailer_config: "RetailerConfig", account_holder: AccountHolder, campaign_slug: str
) -> None:
    time.sleep(3)
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )
    for i in range(len(resp.json()["current_balances"])):
        assert resp.json()["current_balances"][i]["campaign_slug"] != campaign_slug


# fmt: off
@then(parsers.parse("the balance shown for account holder is {amount:d}"))
# fmt: on
def send_get_request_to_accounts_check_balance(
    polaris_db_session: "Session", retailer_config: "RetailerConfig", amount: int
) -> None:
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)
    time.sleep(3)
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )
    for i in range(len(resp.json()["current_balances"])):
        assert resp.json()["current_balances"][i]["value"] == amount


# Retry task fixtures
# fmt: off
@when(parsers.parse("the vela {task_name} task status is {task_status}"))
# fmt: on
def check_vela_retry_task_status_is_cancelled(vela_db_session: "Session", task_name: str, task_status: str) -> None:
    task = get_latest_task(vela_db_session, task_name)
    for i in range(5):
        sleep(i)
        if task.status.value == task_status:
            logging.info(f"{task.status} is {task_status}")
            break
        vela_db_session.refresh(task)
    assert task.status.value == task_status


# fmt: off
@then(parsers.parse("the polaris {task_name} task status is {task_status}"))
# fmt: on
def check_polaris_retry_task_status_is_success(polaris_db_session: "Session", task_name: str, task_status: str) -> None:
    task = get_latest_task(polaris_db_session, task_name)
    for i in range(5):
        sleep(i)
        if task.status.value == task_status:
            logging.info(f"{task.status} is {task_status}")
            break
        polaris_db_session.refresh(task)
    assert task.status.value == task_status


@then(parsers.parse("the {task_name} is retried {num_retried:d} time and successful on attempt {num_success:d}"))
def number_of_callback_attempts(
    polaris_db_session: "Session", task_name: str, num_retried: int, num_success: int
) -> None:
    for i in range(5):
        sleep(i)
        task = get_latest_task(polaris_db_session, task_name)
        if task.attempts == num_success:
            break
    logging.info(f"{task_name} retried number of {num_retried} time ")
    assert task.attempts == num_success
