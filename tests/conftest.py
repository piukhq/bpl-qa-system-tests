import json
import logging
import time

from datetime import datetime
from typing import TYPE_CHECKING, Any, Generator, Literal, Union
from uuid import uuid4

import arrow
import pytest

from pytest_bdd import given, parsers, then, when
from sqlalchemy import create_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import create_database, database_exists, drop_database

import settings

from db.carina.models import Base as CarinaModelBase
from db.carina.models import FetchType, Retailer, RetailerFetchType, Reward, RewardConfig
from db.polaris.models import AccountHolder, AccountHolderCampaignBalance
from db.polaris.models import Base as PolarisModelBase
from db.polaris.models import RetailerConfig
from db.vela.models import Base as VelaModelBase
from db.vela.models import Campaign, EarnRule, RetailerRewards, RewardRule
from settings import (
    CARINA_DATABASE_URI,
    CARINA_TEMPLATE_DB_NAME,
    POLARIS_DATABASE_URI,
    POLARIS_TEMPLATE_DB_NAME,
    VELA_DATABASE_URI,
    VELA_TEMPLATE_DB_NAME,
)
from tests.api.base import Endpoints
from tests.requests.enrolment import send_get_accounts
from tests.requests.transaction import post_transaction_request
from tests.shared_utils.fixture_loader import load_fixture

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import SubRequest
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def polaris_db_session() -> Generator:
    if database_exists(POLARIS_DATABASE_URI):
        logger.info("Dropping Polaris database")
        drop_database(POLARIS_DATABASE_URI)
    logger.info("Creating Polaris database")
    create_database(POLARIS_DATABASE_URI, template=POLARIS_TEMPLATE_DB_NAME)
    engine = create_engine(POLARIS_DATABASE_URI, poolclass=NullPool, echo=False)
    PolarisModelBase.prepare(engine, reflect=True)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session


@pytest.fixture(autouse=True)
def vela_db_session() -> Generator:
    if database_exists(VELA_DATABASE_URI):
        logger.info("Dropping Vela database")
        drop_database(VELA_DATABASE_URI)
    logger.info("Creating Vela database")
    create_database(VELA_DATABASE_URI, template=VELA_TEMPLATE_DB_NAME)
    engine = create_engine(VELA_DATABASE_URI, poolclass=NullPool, echo=False)
    VelaModelBase.prepare(engine, reflect=True)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session


@pytest.fixture(autouse=True)
def carina_db_session() -> Generator:
    if database_exists(CARINA_DATABASE_URI):
        logger.info("Dropping Carina database")
        drop_database(CARINA_DATABASE_URI)
    logger.info("Creating Carina database")
    create_database(CARINA_DATABASE_URI, template=CARINA_TEMPLATE_DB_NAME)
    engine = create_engine(CARINA_DATABASE_URI, poolclass=NullPool, echo=False)
    CarinaModelBase.prepare(engine, reflect=True)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session


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
) -> RetailerConfig:
    fixture_data = load_fixture(retailer_slug)
    retailer_config = RetailerConfig(**fixture_data.retailer_config)
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


# fmt: off
@given(parsers.parse("that retailer has the standard campaigns configured"),
       target_fixture="standard_campaigns",
       )
# fmt: on
def standard_campaigns_and_reward_slugs(
    campaign_slug: str, vela_db_session: "Session", retailer_config: RetailerConfig
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
    retailer_config: RetailerConfig,
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
@given(parsers.parse("the {campaign_slug} campaign has an {campaign_type} earn rule with a threshold of {threshold}, "
                     "an increment of {inc} and a multiplier of {mult}"))
# fmt: on
def create_earn_rule(
    campaign_slug: str, campaign_type: str, threshold: int, inc: int, mult: int, vela_db_session: "Session"
) -> None:
    campaign = vela_db_session.execute(select(Campaign).where(Campaign.slug == campaign_slug)).scalar_one()
    if campaign_type == "STAMPS":
        earn_rule = EarnRule(campaign_id=campaign.id, threshold=threshold, increment=inc, increment_multiplier=mult)
    else:
        earn_rule = EarnRule(campaign_id=campaign.id, threshold=threshold, increment_multiplier=mult)
    vela_db_session.add(earn_rule)
    vela_db_session.commit()


# fmt: off
@given(parsers.parse("the {campaign_slug} campaign has reward rule of {reward_rule}, with reward slug {reward_slug} "
                     "and allocation window {allocation_window}"))
# fmt: on
def create_reward_rule(
    campaign_slug: str, reward_rule: int, reward_slug: str, allocation_window: int, vela_db_session: "Session"
) -> None:
    campaign = vela_db_session.execute(select(Campaign).where(Campaign.slug == campaign_slug)).scalar_one()
    # earn_rule = EarnRule(campaign_id=campaign.id, threshold=threshold, increment=inc, increment_multiplier=mult)
    reward_rule = RewardRule(
        campaign_id=campaign.id, reward_goal=reward_rule, reward_slug=reward_slug, allocation_window=allocation_window
    )
    vela_db_session.add(reward_rule)
    vela_db_session.commit()


# fmt: off
@given(parsers.parse("that campaign has the standard reward config configured with {reward_n:d} allocable rewards"),
       target_fixture="standard_reward_configs",
       )
# fmt: on
def standard_reward_and_reward_config(
    carina_db_session: "Session",
    reward_n: int,
    retailer_config: RetailerConfig,
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
    carina_db_session: "Session", retailer_config: RetailerConfig, request_context: dict
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


@pytest.fixture(scope="session", autouse=True)
def configure_html_report_env(request: "SubRequest", env: str, channel: str) -> None:
    """Delete existing data in the test report and add bpl execution details"""

    metadata: dict = getattr(request.config, "_metadata")

    for ele in list(metadata.keys()):
        del metadata[ele]
    # if re.search(r'^(GITLAB_|CI_)', k): for git lab related extra table contents
    metadata.update({"Test Environment": env.upper(), "Channel": channel})


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
    retailer_config: RetailerConfig,
    polaris_db_session: "Session",
    vela_db_session: "Session",
) -> AccountHolder:

    account_status = {"active": "ACTIVE", "pending": "PENDING", "inactive": "INACTIVE"}.get(status, "PENDING")

    account_holder = AccountHolder(
        email=f"pytest+{uuid4()}@bink.com",
        status=account_status,
        account_number="1234567890",
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


@when(parsers.parse("BPL receives a transaction for the account holder for the amount of {amount:d} pennies"))
def the_account_holder_transaction_request(
    account_holder: AccountHolder, retailer_config: RetailerConfig, amount: int, request_context: dict
) -> None:

    payload = {
        "id": str(uuid4()),
        "transaction_total": amount,
        "datetime": int(datetime.utcnow().timestamp()),
        "MID": "12432432",
        "loyalty_id": str(account_holder.account_holder_uuid),
    }
    logging.info(f"Payload of transaction : {json.dumps(payload)}")
    post_transaction_request(payload, retailer_config.slug, request_context)


# fmt: off
@then(parsers.parse("{expected_num_rewards:d} rewards are available to the account holder"))
# fmt: on
def send_get_request_to_account_holder(
    retailer_config: RetailerConfig, account_holder: AccountHolder, expected_num_rewards: int
) -> None:
    time.sleep(3)
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )
    assert len(resp.json()["rewards"]) == expected_num_rewards
    for i in range(expected_num_rewards):
        assert resp.json()["rewards"][i]["code"]
        assert resp.json()["rewards"][i]["issued_date"]
        assert resp.json()["rewards"][i]["redeemed_date"] is None
        assert resp.json()["rewards"][i]["expiry_date"]
        assert resp.json()["rewards"][i]["status"] == "issued"


@then(parsers.parse("the account holder's {campaign_slug} balance is {amount:d}"))
def account_holder_balance_correct(
    polaris_db_session: "Session", account_holder: AccountHolder, campaign_slug: str, amount: int
) -> None:
    polaris_db_session.refresh(account_holder)
    balances_by_slug = {ahcb.campaign_slug: ahcb for ahcb in account_holder.accountholdercampaignbalance_collection}
    assert balances_by_slug[campaign_slug].balance == amount
