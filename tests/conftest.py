import importlib
import json
import logging
import random
import time
import uuid

from datetime import datetime, timedelta, timezone
from time import sleep
from typing import TYPE_CHECKING, Any, Callable, Generator, Literal
from uuid import uuid4

import arrow
import pytest
import yaml

from azure.storage.blob import BlobClient
from faker import Faker
from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from redis import Redis
from retry_tasks_lib.utils.synchronous import enqueue_many_retry_tasks, sync_create_many_tasks
from sqlalchemy import create_engine, update
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import create_database, database_exists, drop_database

import settings

from azure_actions.blob_storage import add_new_available_rewards_file, put_new_reward_updates_file
from db.carina import models as carina_models
from db.carina.models import FetchType, Retailer, RetailerFetchType, Reward, RewardCampaign, RewardConfig
from db.hubble import models as hubble_models
from db.polaris import models as polaris_models
from db.polaris.models import (
    AccountHolder,
    AccountHolderCampaignBalance,
    AccountHolderProfile,
    EmailTemplate,
    EmailTemplateKey,
    EmailTemplateRequiredKey,
    RetailerConfig,
)
from db.vela import models as vela_models
from db.vela.models import Campaign, EarnRule, RetailerRewards, RewardRule
from settings import (
    BLOB_STORAGE_DSN,
    CARINA_DATABASE_URI,
    CARINA_TEMPLATE_DB_NAME,
    HUBBLE_DATABASE_URI,
    HUBBLE_TEMPLATE_DB_NAME,
    MOCK_SERVICE_BASE_URL,
    POLARIS_DATABASE_URI,
    POLARIS_TEMPLATE_DB_NAME,
    REDIS_URL,
    SQL_DEBUG,
    VELA_DATABASE_URI,
    VELA_TEMPLATE_DB_NAME,
    redis,
)
from tests.api.base import Endpoints, get_callback_url
from tests.db_actions.carina import get_fetch_type_id, get_retailer_id, get_reward_config_id
from tests.db_actions.polaris import (
    create_balance_for_account_holder,
    create_pending_rewards_for_existing_account_holder,
    create_rewards_for_existing_account_holder,
)
from tests.db_actions.vela import get_campaign_by_slug
from tests.requests.enrolment import send_get_accounts, send_post_enrolment
from tests.requests.status_change import send_post_campaign_status_change
from tests.requests.transaction import post_transaction_request
from tests.shared_utils.fixture_loader import load_fixture
from tests.shared_utils.redis import pause_redis, unpause_redis

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)

fake = Faker(locale="en_GB")


# SETUP
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
@given(parse("the {retailer_slug} retailer exists"),
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


@given(parse("the task worker queue is full"))
@when(parse("the task worker queue is full"))
def stop_redis() -> None:
    pause_redis(seconds=10)


@given(parse("the task worker queue is ready"))
@when(parse("the task worker queue is ready"))
def resume_redis() -> None:
    unpause_redis()
    secs = 5
    logger.info(f"Sleeping {secs} seconds to allow queued tasks to run...")
    sleep(secs)


# HOOKS
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


# CARINA FIXTURES
# fmt: off
@given(parse("the retailer has a {reward_slug} reward config configured with {required_fields_values}, "
             "and a status of {status} and a {fetch_type_name} fetch type"))
# fmt: on
def add_reward_config(
    carina_db_session: "Session",
    reward_slug: str,
    required_fields_values: str,
    status: str,
    retailer_config: RetailerConfig,
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
@given(parse("a {fetch_type_name} fetch type is configured for the current retailer with an agent config "
             "brand id {brand_id:d}"))
# fmt: on
def add_retailer_fetch_type_egift(
    carina_db_session: "Session",
    retailer_config: RetailerConfig,
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
@given(parse("a {fetch_type_name} fetch type is configured for the current retailer with an agent config of "
             "{agent_config}"))
# fmt: on
def add_retailer_fetch_type_preloaded(
    carina_db_session: "Session",
    retailer_config: RetailerConfig,
    fetch_type_name: str,
    agent_config: str | None,
) -> None:

    retailer_fetch_type = RetailerFetchType(
        retailer_id=get_retailer_id(carina_db_session=carina_db_session, retailer_slug=retailer_config.slug),
        fetch_type_id=get_fetch_type_id(carina_db_session=carina_db_session, fetch_type_name=fetch_type_name),
        agent_config=agent_config,
    )
    carina_db_session.add(retailer_fetch_type)
    carina_db_session.commit()


# fmt: off
@when(parse("{rewards_n:d} rewards are generated for the {reward_slug} reward config with allocation status "
            "set to {allocation_status} and deleted status set to {deleted_status}"),
      target_fixture="available_rewards")
@given(parse(
    "there is {rewards_n:d} rewards configured for the {reward_slug} reward config, with allocation status set to "
    "{allocation_status} and deleted status set to {deleted_status}"),
    target_fixture="available_rewards")
# fmt: on
def add_rewards(
    carina_db_session: "Session",
    reward_slug: str,
    allocation_status: str,
    deleted_status: str,
    retailer_config: RetailerConfig,
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
@given(parse("that campaign has the standard reward config configured with {reward_n:d} allocable rewards"),
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
@given(parse("required fetch type are configured for the current retailer"),
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


@pytest.fixture(scope="function")
def upload_reward_updates_to_blob_storage() -> Callable:
    def func(retailer_slug: str, rewards: list[Reward], reward_status: str, blob_name: str = None) -> BlobClient | None:
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


@pytest.fixture(scope="function")
def upload_rewards_to_blob_storage() -> Callable:
    def func(retailer_slug: str, codes: list[str], *, reward_slug: str, expired_date: str) -> BlobClient | None:
        """Upload some new reward codes to blob storage to test end-to-end import"""
        blob = None

        if BLOB_STORAGE_DSN:
            logger.debug(
                f"Uploading reward import file to blob storage for {retailer_slug} " f"(reward slug: {reward_slug})..."
            )
            blob = add_new_available_rewards_file(retailer_slug, codes, reward_slug, expired_date)
            logger.debug(f"Successfully uploaded new reward codes to blob storage: {blob.url}")
        else:
            logger.debug("No BLOB_STORAGE_DSN set, skipping reward updates upload")

        return blob

    return func


# fmt: off
@when(parse("the {retailer_slug} retailer updates selected rewards to {reward_status} status"),
      target_fixture="imported_reward_ids")
# fmt: on
def reward_updates_upload(
    retailer_slug: str,
    reward_status: str,
    available_rewards: list[Reward],
    upload_reward_updates_to_blob_storage: Callable,
) -> list[str]:
    """
    The fixture should place a CSV file onto blob storage, which a running instance of
    carina (the scheduler job for doing these imports) will pick up and process, putting rows into carina's DB
    for today's date.
    """
    blob = upload_reward_updates_to_blob_storage(
        retailer_slug=retailer_slug, rewards=available_rewards, reward_status=reward_status
    )
    assert blob
    return [reward.id for reward in available_rewards]


# fmt: off
@given(
    parse(
        "the retailer provides {num_rewards:d} rewards in a csv file for the {reward_slug} "
        "reward slug with rewards expiry date {expired_date}"
    )
)
# fmt: on
def add_new_rewards_via_azure_blob(
    num_rewards: int,
    retailer_config: RetailerConfig,
    reward_slug: str,
    expired_date: str,
    upload_rewards_to_blob_storage: Callable,
) -> None:
    reward_expired_date = None if expired_date == "None" else expired_date
    new_rewards_codes = [str(uuid.uuid4()) for _ in range(num_rewards)]
    blob = upload_rewards_to_blob_storage(
        retailer_slug=retailer_config.slug,
        codes=new_rewards_codes,
        reward_slug=reward_slug,
        expired_date=reward_expired_date,
    )
    time.sleep(20)
    assert blob


# POLARIS FIXTURES
# fmt: off
@given(parse("an {status} account holder exists for the retailer"),
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

    ah_profile = AccountHolderProfile(
        account_holder_id=account_holder.id, first_name=fake.first_name(), last_name=fake.last_name()
    )
    polaris_db_session.add(ah_profile)
    polaris_db_session.commit()

    campaigns = (
        vela_db_session.execute(
            select(Campaign).where(Campaign.retailer_id == retailer_config.id, Campaign.status == "ACTIVE")
        )
        .scalars()
        .all()
    )
    for campaign in campaigns:
        create_balance_for_account_holder(polaris_db_session, account_holder, campaign)
    return account_holder


# fmt: off
@given(parse("the retailer has {num_account_holders:d} {status} account holders"),
       target_fixture="account_holders")
# fmt: on
def make_multiple_account_holders(
    retailer_config: RetailerConfig,
    polaris_db_session: "Session",
    vela_db_session: "Session",
    num_account_holders: int,
    status: str,
) -> list["AccountHolder"]:
    account_holders: list[AccountHolder] = []
    for i in range(num_account_holders):
        account_holders.append(
            setup_account_holder(
                status,
                retailer_config=retailer_config,
                polaris_db_session=polaris_db_session,
                vela_db_session=vela_db_session,
            )
        )
    return account_holders


# fmt: off
@when(parse("an account holder is enrolled passing in all required and optional fields with a callback URL for "
            "{num_failures:d} consecutive HTTP {status_code:d} responses"))
# fmt: on
def post_enrolment_with_known_repeated_callback(
    retailer_config: RetailerConfig, num_failures: int, status_code: int
) -> None:
    enrol_account_holder(
        retailer_config, callback_url=get_callback_url(num_failures=num_failures, status_code=status_code)
    )


@given(parse("I enrol an account holder passing in all required and all optional fields"))
@when(parse("I enrol an account holder passing in all required and all optional fields"))
@when(parse("the account holder enrol to retailer with all required and all optional fields"))
def enrol_accountholder_with_all_required_fields(retailer_config: RetailerConfig) -> None:
    return enrol_account_holder(retailer_config)


def enrol_account_holder(
    retailer_config: RetailerConfig,
    incl_optional_fields: bool = True,
    callback_url: str | None = None,
) -> None:
    if incl_optional_fields:
        request_body = all_required_and_all_optional_credentials(callback_url=callback_url)
    else:
        request_body = only_required_credentials()
    resp = send_post_enrolment(retailer_config.slug, request_body)
    time.sleep(3)
    logging.info(
        f"Response HTTP status code for enrolment: {resp.status_code} "
        f"Response status: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.status_code == 202
    logging.info(f"Account holder response: {resp}")


def all_required_and_all_optional_credentials(callback_url: str | None = None) -> dict:
    payload = {
        "credentials": _get_credentials(),
        "marketing_preferences": [{"key": "marketing_pref", "value": True}],
        "callback_url": callback_url or f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("`Request body for POST Enrol: " + json.dumps(payload, indent=4))
    return payload


def _get_credentials() -> dict:
    return {
        "email": f"qa_pytest_{uuid4()}@bink.com",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
    }


def only_required_credentials() -> dict:
    credentials = _get_credentials()
    del credentials["address_line2"]
    del credentials["postcode"]
    del credentials["city"]
    payload = {
        "credentials": credentials,
        "marketing_preferences": [{"key": "marketing_pref", "value": True}],
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("Request body for POST Enrol: " + json.dumps(payload, indent=4))
    return payload


# fmt: off
@given(parse("the account holders each have {num_rewards:d} {reward_status} rewards for the {campaign_slug} "
             "campaign with the {reward_slug} reward slug expiring {expiring}"))
# fmt: on
def make_account_holder_rewards(
    retailer_config: RetailerConfig,
    account_holders: list[AccountHolder],
    polaris_db_session: "Session",
    num_rewards: int,
    reward_status: str,
    campaign_slug: str,
    reward_slug: str,
    expiring: str,
) -> None:
    for account_holder in account_holders:
        create_rewards_for_existing_account_holder(
            polaris_db_session,
            retailer_slug=retailer_config.slug,
            reward_count=num_rewards,
            account_holder_id=account_holder.id,
            campaign_slug=campaign_slug,
            reward_slug=reward_slug,
            status=reward_status,
            expiry_date=arrow.utcnow().dehumanize(expiring).datetime,
        )


# fmt: off
@given(parse("the account holders each have {num_rewards:d} pending rewards for the {campaign_slug} campaign "
             "and {reward_slug} reward slug with a value of {value:d}"))
# fmt: on
def make_account_holder_pending_rewards(
    retailer_config: RetailerConfig,
    account_holders: list[AccountHolder],
    polaris_db_session: "Session",
    num_rewards: int,
    campaign_slug: str,
    reward_slug: str,
    value: int,
) -> None:
    for account_holder in account_holders:
        create_pending_rewards_for_existing_account_holder(
            polaris_db_session, retailer_config.slug, num_rewards, account_holder.id, campaign_slug, reward_slug, value
        )


# fmt: off
@given(parse("the retailer has a {email_type} email template configured with template id {template_id}"))
# fmt: on
def create_email_template(
    email_type: str,
    template_id: str,
    polaris_db_session: "Session",
    retailer_config: "RetailerConfig",
) -> None:

    template = EmailTemplate(template_id=template_id, type=email_type, retailer_id=retailer_config.id)
    polaris_db_session.add(template)
    polaris_db_session.commit()


# fmt: off
@given(parse("the email template with template id {template_id} has the following required template variables: "
             "{comma_sep_template_variables}"))
# fmt: on
def add_vars_to_email_template(
    retailer_config: RetailerConfig, polaris_db_session: "Session", template_id: str, comma_sep_template_variables: str
) -> None:
    email_var_names = [evn.strip() for evn in comma_sep_template_variables.split(",")]

    keys = (
        polaris_db_session.execute(select(EmailTemplateKey.id).where(EmailTemplateKey.name.in_(email_var_names)))
        .scalars()
        .all()
    )

    email_template = polaris_db_session.execute(
        select(EmailTemplate).where(
            EmailTemplate.template_id == template_id, EmailTemplate.retailer_id == retailer_config.id
        )
    ).scalar_one()

    for key in keys:
        required_key = EmailTemplateRequiredKey(email_template_id=email_template.id, email_template_key_id=key)
        polaris_db_session.add(required_key)

    polaris_db_session.commit()


# fmt: off
@given(parse("the account has {reward_count} issued unexpired rewards for the {campaign_slug} campaign"))
# fmt: on
def update_existing_account_holder_with_rewards(
    account_holder: AccountHolder,
    retailer_config: RetailerConfig,
    reward_count: int,
    campaign_slug: str,
    polaris_db_session: "Session",
) -> AccountHolder:

    create_rewards_for_existing_account_holder(
        polaris_db_session,
        retailer_slug=retailer_config.slug,
        reward_count=reward_count,
        account_holder_id=account_holder.id,
        campaign_slug=campaign_slug,
    )

    return account_holder


# fmt: off
@given(parse("the account has {count} pending rewards for the {campaign_slug} campaign and {reward_slug} "
             "reward slug with value {reward_goal}"))
# fmt: on
def update_existing_account_holder_with_pending_rewards(
    account_holder: AccountHolder,
    retailer_config: RetailerConfig,
    count: int,
    polaris_db_session: "Session",
    reward_goal: int,
    campaign_slug: str,
    reward_slug: str,
) -> AccountHolder:

    create_pending_rewards_for_existing_account_holder(
        polaris_db_session, retailer_config.slug, count, account_holder.id, campaign_slug, reward_slug, reward_goal
    )

    return account_holder


# fmt: off
@given(parse("the account holder's {campaign_slug} balance is {amount:d}"))
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


# fmt: off
@then(parse("{expected_num_rewards:d} reward for the account holder shows as {reward_status} "
            "with redeemed date"))
# fmt: on
def verify_account_holder_reward_status(
    retailer_config: RetailerConfig, account_holder: AccountHolder, expected_num_rewards: int, reward_status: str
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
@given(parse("there are {reward_count} issued unexpired rewards for account holder with "
             "reward slug {reward_slug} and campaign slug {campaign_slug}"))
# fmt: on
def update_existing_account_holder_with_rewards_for_reward_slug(
    account_holder: AccountHolder,
    retailer_config: RetailerConfig,
    reward_count: int,
    reward_slug: str,
    campaign_slug: str,
    polaris_db_session: "Session",
) -> AccountHolder:
    create_rewards_for_existing_account_holder(
        polaris_db_session,
        retailer_slug=retailer_config.slug,
        reward_count=reward_count,
        account_holder_id=account_holder.id,
        campaign_slug=campaign_slug,
        reward_slug=reward_slug,
    )
    return account_holder


# VELA FIXTURES
# fmt: off
@given(parse("that retailer has the standard campaigns configured"),
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
@given(parse("the retailer's {campaign_slug} {loyalty_type} campaign starts {starts_when} and ends "
             "{ends_when} and is {status}"), target_fixture="standard_campaign")
# fmt: on
def create_campaign(
    campaign_slug: str,
    loyalty_type: Literal["STAMPS"] | Literal["ACCUMULATOR"],
    starts_when: str,
    ends_when: str,
    status: str,
    vela_db_session: "Session",
    retailer_config: "RetailerConfig",
) -> Campaign:

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

    return campaign


# fmt: off
@given(parse("the retailer's {campaign_slug} campaign with reward_slug: {reward_slug} added as {status}"))
# fmt: on
def create_reward_campaign(
    campaign_slug: str,
    reward_slug: str,
    status: str,
    carina_db_session: "Session",
    retailer_config: "RetailerConfig",
) -> RewardCampaign:
    campaign_reward = RewardCampaign(
        retailer_id=retailer_config.id,
        campaign_slug=campaign_slug,
        reward_slug=reward_slug,
        campaign_status=status,
    )
    carina_db_session.add(campaign_reward)
    carina_db_session.commit()

    return campaign_reward


# fmt: off
@given(parse("the {campaign_slug} campaign has an earn rule with a threshold of {threshold:d}, an increment of {inc}, "
             "a multiplier of {mult:d} and max amount of {earn_max_amount:d}"))
# fmt: on
def create_earn_rule(
    vela_db_session: "Session",
    campaign_slug: str,
    threshold: int,
    inc: str,
    mult: int,
    earn_max_amount: int,
) -> None:
    converted_inc = None if inc == "None" else int(inc)
    campaign = vela_db_session.execute(select(Campaign).where(Campaign.slug == campaign_slug)).scalar_one()
    earn_rule = EarnRule(
        campaign_id=campaign.id,
        threshold=threshold,
        increment=converted_inc,
        increment_multiplier=mult,
        max_amount=earn_max_amount,
    )

    vela_db_session.add(earn_rule)
    vela_db_session.commit()


# fmt: off
@given(parse("the {campaign_slug} campaign has reward rule with reward goal: {reward_goal:d}, reward slug: "
             "{reward_slug}, allocation window: {allocation_window:d} and reward cap: {reward_cap}"))
# fmt: on
def create_reward_rule(
    vela_db_session: "Session",
    campaign_slug: str,
    reward_goal: int,
    reward_slug: str,
    allocation_window: int,
    reward_cap: str,
) -> None:
    campaign = get_campaign_by_slug(vela_db_session=vela_db_session, campaign_slug=campaign_slug)
    reward_goal = RewardRule(
        campaign_id=campaign.id,
        reward_goal=reward_goal,
        reward_slug=reward_slug,
        allocation_window=allocation_window,
        reward_cap=reward_cap if int(reward_cap) > 0 else None,
    )
    vela_db_session.add(reward_goal)
    vela_db_session.commit()


@given(parse("BPL receives a transaction for the account holder for the amount of {amount} pennies"))
@when(parse("BPL receives a transaction for the account holder for the amount of {amount} pennies"))
def the_account_holder_transaction_request(
    account_holder: AccountHolder, retailer_config: RetailerConfig, amount: int, request_context: dict
) -> None:
    time.sleep(3)
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
@given(parse("the retailer's {campaign_slug} campaign status is changed to {status}"))
@when(parse("the retailer's {campaign_slug} campaign status is changed to {status}"))
# fmt: on
def send_post_campaign_change_request(
    request_context: dict,
    status: str,
    retailer_config: RetailerConfig,
    campaign_slug: str,
) -> None:
    payload: dict[str, Any] = {
        "requested_status": status,
        "campaign_slugs": [campaign_slug],
        "activity_metadata": {"sso_username": "qa_auto"}
    }

    request = send_post_campaign_status_change(
        request_context=request_context, retailer_slug=retailer_config.slug, request_body=payload
    )
    assert request.status_code == 200


# RETRY TASK FIXTURES
# fmt: off
@when(parse("each account holder has a queued reward-adjustment task for the {campaign_slug} campaign with an "
            "adjustment amount of {adjustment_amount:d}"))
# fmt: on
def enqueue_reward_adjustment_tasks_for_account_holders(
    retailer_config: RetailerConfig,
    vela_db_session: "Session",
    account_holders: list[AccountHolder],
    campaign_slug: str,
    adjustment_amount: int,
) -> None:
    task_params_list = [
        {
            "processed_transaction_id": list(range(len(account_holders)))[i],
            "retailer_slug": retailer_config.slug,
            "adjustment_amount": adjustment_amount,
            "campaign_slug": campaign_slug,
            "account_holder_uuid": ah.account_holder_uuid,
            "transaction_datetime": datetime.now(tz=timezone.utc),
        }
        for i, ah in enumerate(account_holders)
    ]
    logging.info("Making reward-adjustment tasks...")
    tasks = sync_create_many_tasks(vela_db_session, task_type_name="reward-adjustment", params_list=task_params_list)
    vela_db_session.commit()
    logging.info("Enqueueing reward-adjustment tasks...")
    redis = Redis.from_url(REDIS_URL)
    enqueue_many_retry_tasks(vela_db_session, retry_tasks_ids=[task.retry_task_id for task in tasks], connection=redis)


# fmt: off
@when(parse("there are reward-issuance tasks for the account holders for the {reward_slug} reward slug "
            "and {campaign_slug} campaign_slug on the queue"))
# fmt: on
def enqueue_reward_issuance_tasks_for_account_holders(
    retailer_config: RetailerConfig,
    carina_db_session: "Session",
    account_holders: list[AccountHolder],
    reward_slug: str,
    campaign_slug: str,
) -> None:
    reward_config_id = carina_db_session.execute(
        select(RewardConfig.id)
        .join(Retailer)
        .where(RewardConfig.reward_slug == reward_slug, Retailer.slug == retailer_config.slug)
    ).scalar()
    task_params_list = [
        {
            "code": str(uuid4()),
            "expiry_date": (datetime.now(tz=timezone.utc) + timedelta(days=1)).timestamp(),
            "reward_uuid": str(uuid4()),
            "reward_slug": reward_slug,
            "retailer_slug": retailer_config.slug,
            "campaign_slug": campaign_slug,
            "reward_config_id": reward_config_id,
            "issued_date": datetime.now(tz=timezone.utc).timestamp(),
            "account_url": (
                f"{settings.POLARIS_BASE_URL}/{retailer_config.slug}/accounts/{ah.account_holder_uuid}/rewards"
            ),
            "idempotency_token": str(uuid4()),
            "agent_state_params_raw": json.dumps(
                {
                    "associated_url": (
                        "http://dummy-reward-provider-site/reward"
                        f"?retailer={retailer_config.slug}&reward=a96c90cf-0944-44de-a180-bae2ed93816e"
                    )
                }
            ),
        }
        for ah in account_holders
    ]
    logging.info("Making reward-issuance tasks...")
    tasks = sync_create_many_tasks(carina_db_session, task_type_name="reward-issuance", params_list=task_params_list)
    carina_db_session.add_all(tasks)
    carina_db_session.commit()
    logging.info("Enqueueing reward-issuance tasks...")
    enqueue_many_retry_tasks(
        carina_db_session, retry_tasks_ids=[task.retry_task_id for task in tasks], connection=redis
    )
