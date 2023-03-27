import importlib
import json
import logging
import random
import time
import uuid

from datetime import datetime
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
from retry_tasks_lib.utils.synchronous import enqueue_many_retry_tasks, sync_create_many_tasks
from sqlalchemy import create_engine, delete, update
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import create_database, database_exists, drop_database

import settings

from azure_actions.blob_storage import add_new_available_rewards_file, put_new_reward_updates_file
from db.cosmos import models as cosmos_models
from db.cosmos.models import (
    AccountHolder,
    AccountHolderProfile,
    Campaign,
    CampaignBalance,
    EarnRule,
    EmailTemplate,
    EmailTemplateKey,
    EmailTemplateRequiredKey,
    Retailer,
    RetailerFetchType,
    RetailerStore,
    Reward,
    RewardConfig,
    RewardRule,
)
from db.hubble import models as hubble_models
from settings import (
    BLOB_STORAGE_DSN,
    COSMOS_DATABASE_URI,
    COSMOS_TEMPLATE_DB_NAME,
    HUBBLE_DATABASE_URI,
    HUBBLE_TEMPLATE_DB_NAME,
    MOCK_SERVICE_BASE_URL,
    SQL_DEBUG,
)
from tests.api.base import Endpoints, get_callback_url
from tests.db_actions.cosmos import (
    create_balance_for_account_holder,
    create_pending_rewards_for_existing_account_holder,
    create_rewards_for_existing_account_holder,
    get_campaign_by_slug,
    get_fetch_type_id,
    get_retailer_id,
)
from tests.db_actions.reward import assign_rewards
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
def cosmos_db_session() -> Generator:
    if database_exists(COSMOS_DATABASE_URI):
        logger.info("Dropping Cosmos database")
        drop_database(COSMOS_DATABASE_URI)
    logger.info("Creating Cosmos database")
    create_database(COSMOS_DATABASE_URI, template=COSMOS_TEMPLATE_DB_NAME)
    engine = create_engine(COSMOS_DATABASE_URI, poolclass=NullPool, echo=SQL_DEBUG)
    cosmos_models.Base.prepare(autoload_with=engine)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session
    importlib.reload(cosmos_models)


@pytest.fixture(autouse=True)
def hubble_db_session() -> Generator:
    engine = create_engine(HUBBLE_DATABASE_URI, poolclass=NullPool, echo=SQL_DEBUG)
    with sessionmaker(bind=engine)() as db_session:
        if not database_exists(HUBBLE_DATABASE_URI):
            logger.info("Creating Hubble database")
            create_database(HUBBLE_DATABASE_URI, template=HUBBLE_TEMPLATE_DB_NAME)
        else:
            logger.info("Truncating Hubble activity table")
            db_session.execute(delete(hubble_models.Activity.__table__))
        hubble_models.Base.prepare(autoload_with=engine)
        yield db_session


# This is the only way I could get the cucumber plugin to work
# in vscode with target_fixture and play nice with flake8
# https://github.com/alexkrechik/VSCucumberAutoComplete/issues/373
# fmt: off
@given(parse("the {retailer_slug} retailer exists with status as {status}"),
       target_fixture="retailer_config",
       )
# fmt: on
def retailer(
    cosmos_db_session: "Session",
    retailer_slug: str,
    status: str,
    request_context: dict,
) -> Retailer:
    fixture_data = load_fixture(retailer_slug)
    fixture_data.retailer["status"] = status
    retailer = Retailer(**fixture_data.retailer)
    cosmos_db_session.add(retailer)
    cosmos_db_session.commit()
    logging.info(retailer)
    # request_context["cosmos_retailer_id"] = retailer.id
    return retailer


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


# fmt: off
@given(parse("the retailer has a {reward_slug} reward config configured with {required_fields_values}, "
             "and a status of {status} and a {fetch_type_name} fetch type"), target_fixture="reward_config",)
# fmt: on
def add_reward_config(
    cosmos_db_session: "Session",
    reward_slug: str,
    required_fields_values: str,
    status: str,
    retailer_config: Retailer,
    fetch_type_name: str,
) -> RewardConfig:
    retailer_id = get_retailer_id(cosmos_db_session=cosmos_db_session, retailer_slug=retailer_config.slug)
    fetch_type_id = get_fetch_type_id(cosmos_db_session=cosmos_db_session, fetch_type_name=fetch_type_name)

    if status not in {"ACTIVE", "INACTIVE"}:
        raise ValueError("Invalid Status")

    reward_config = RewardConfig(
        slug=reward_slug,
        retailer_id=retailer_id,
        active=status == "ACTIVE",
        required_fields_values=required_fields_values,
        fetch_type_id=fetch_type_id,
    )
    cosmos_db_session.add(reward_config)
    cosmos_db_session.commit()
    return reward_config


# fmt: off
@given(parse("a {fetch_type_name} fetch type is configured for the current retailer with an agent config "
             "brand id {brand_id:d}"))
# fmt: on
def add_retailer_fetch_type_egift(
    cosmos_db_session: "Session",
    retailer_config: Retailer,
    fetch_type_name: str,
    brand_id: int,
) -> None:

    agent_config = {"base_url": settings.API_REFLECTOR_BASE_URL, "brand_id": brand_id}

    retailer_fetch_type = RetailerFetchType(
        retailer_id=get_retailer_id(cosmos_db_session=cosmos_db_session, retailer_slug=retailer_config.slug),
        fetch_type_id=get_fetch_type_id(cosmos_db_session=cosmos_db_session, fetch_type_name=fetch_type_name),
        agent_config=yaml.dump(agent_config),
    )
    cosmos_db_session.add(retailer_fetch_type)
    cosmos_db_session.commit()


# fmt: off
@given(parse("a {fetch_type_name} fetch type is configured for the current retailer with an agent config of "
             "{agent_config}"))
# fmt: on
def add_retailer_fetch_type_preloaded(
    cosmos_db_session: "Session",
    retailer_config: Retailer,
    fetch_type_name: str,
    agent_config: str | None,
) -> None:

    retailer_fetch_type = RetailerFetchType(
        retailer_id=get_retailer_id(cosmos_db_session=cosmos_db_session, retailer_slug=retailer_config.slug),
        fetch_type_id=get_fetch_type_id(cosmos_db_session=cosmos_db_session, fetch_type_name=fetch_type_name),
        agent_config=agent_config,
    )
    cosmos_db_session.add(retailer_fetch_type)
    cosmos_db_session.commit()


# fmt: off
@given(parse("{rewards_n:d} {account_holder} rewards are generated for the {reward_slug} "
             "reward config with deleted status set to {deleted_status}"), target_fixture="available_rewards")
# fmt: on
def add_rewards(
    cosmos_db_session: "Session",
    account_holder: AccountHolder,
    reward_slug: str,
    deleted_status: str,
    retailer_config: Retailer,
    standard_campaign: Campaign,
    rewards_n: int,
) -> list[Reward]:
    if account_holder == "unassigned":
        rewards = assign_rewards(
            cosmos_db_session,
            reward_slug,
            retailer_config,
            standard_campaign,
            rewards_n,
            deleted_status,
            account_holder=None,
        )
    else:
        rewards = assign_rewards(
            cosmos_db_session,
            reward_slug,
            retailer_config,
            standard_campaign,
            rewards_n,
            deleted_status,
            account_holder,
        )
    logging.info(f"{rewards_n} rewards attached to {rewards}")
    return rewards


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
    retailer_config: Retailer,
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
    assert blob


# fmt: off
@given(parse("an {status} account holder exists for the retailer"),
       target_fixture="account_holder",
       )
# fmt: on
def setup_account_holder(
    status: str,
    retailer_config: Retailer,
    cosmos_db_session: "Session",
) -> AccountHolder:

    account_status = {"active": "ACTIVE", "pending": "PENDING", "inactive": "INACTIVE"}.get(status, "PENDING")
    fixture_data = load_fixture(retailer_config.slug)
    account_holder = AccountHolder(
        email=f"pytest+{uuid4()}@bink.com",
        status=account_status,
        account_number=fixture_data.retailer["account_number_prefix"] + str(random.randint(1, (10**10))),
        retailer_id=retailer_config.id,
        account_holder_uuid=str(uuid4()),
        opt_out_token=str(uuid4()),
    )
    cosmos_db_session.add(account_holder)
    cosmos_db_session.flush()

    ah_profile = AccountHolderProfile(
        account_holder_id=account_holder.id, first_name=fake.first_name(), last_name=fake.last_name()
    )
    cosmos_db_session.add(ah_profile)
    cosmos_db_session.commit()

    campaigns = (
        cosmos_db_session.execute(
            select(Campaign).where(Campaign.retailer_id == retailer_config.id, Campaign.status == "ACTIVE")
        )
        .scalars()
        .all()
    )
    for campaign in campaigns:
        create_balance_for_account_holder(cosmos_db_session, account_holder, campaign)
    return account_holder


# fmt: off
@given(parse("the retailer has {num_account_holders:d} {status} account holders"),
       target_fixture="account_holders")
# fmt: on
def make_multiple_account_holders(
    retailer_config: Retailer,
    cosmos_db_session: "Session",
    num_account_holders: int,
    status: str,
) -> list["AccountHolder"]:
    account_holders: list[AccountHolder] = []
    for i in range(num_account_holders):
        account_holders.append(
            setup_account_holder(
                status,
                retailer_config=retailer_config,
                cosmos_db_session=cosmos_db_session,
            )
        )
    return account_holders


# fmt: off
@when(parse("an account holder is enrolled passing in all required and optional fields with a callback URL for "
            "{num_failures:d} consecutive HTTP {status_code:d} responses"))
# fmt: on
def post_enrolment_with_known_repeated_callback(retailer_config: Retailer, num_failures: int, status_code: int) -> None:
    enrol_account_holder(
        retailer_config, callback_url=get_callback_url(num_failures=num_failures, status_code=status_code)
    )


@given(parse("I enrol an account holder passing in all required and all optional fields"))
@when(parse("I enrol an account holder passing in all required and all optional fields"))
@when(parse("the account holder enrol to retailer with all required and all optional fields"))
def enrol_accountholder_with_all_required_fields(retailer_config: Retailer) -> None:
    return enrol_account_holder(retailer_config)


def enrol_account_holder(
    retailer_config: Retailer,
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
    retailer_config: Retailer,
    account_holders: list[AccountHolder],
    cosmos_db_session: "Session",
    num_rewards: int,
    reward_status: str,
    campaign_slug: str,
    reward_slug: str,
    expiring: str,
) -> None:
    for account_holder in account_holders:
        create_rewards_for_existing_account_holder(
            cosmos_db_session,
            retailer_slug=retailer_config.slug,
            reward_count=num_rewards,
            account_holder_id=account_holder.id,
            campaign_slug=campaign_slug,
            reward_slug=reward_slug,
            expiry_date=arrow.utcnow().dehumanize(expiring).datetime,
        )


# fmt: off
@given(parse("the account holders each have {num_rewards:d} pending rewards for the {campaign_slug} campaign "
             "and {reward_slug} reward slug with a value of {value:d}"))
# fmt: on
def make_account_holder_pending_rewards(
    retailer_config: Retailer,
    account_holders: list[AccountHolder],
    cosmos_db_session: "Session",
    num_rewards: int,
    campaign_slug: str,
    reward_slug: str,
    value: int,
) -> None:
    for account_holder in account_holders:
        create_pending_rewards_for_existing_account_holder(
            cosmos_db_session, num_rewards, account_holder.id, campaign_slug, value
        )


# fmt: off
@given(parse("the retailer has a {email_type} email template configured with template id {template_id}"))
# fmt: on
def create_email_template(
    email_type: str,
    template_id: str,
    cosmos_db_session: "Session",
    retailer_config: Retailer,
) -> None:

    template = EmailTemplate(template_id=template_id, type=email_type, retailer_id=retailer_config.id)
    cosmos_db_session.add(template)
    cosmos_db_session.commit()


# fmt: off
@given(parse("the email template with template id {template_id} has the following required template variables: "
             "{comma_sep_template_variables}"))
# fmt: on
def add_vars_to_email_template(
    retailer_config: Retailer, cosmos_db_session: "Session", template_id: str, comma_sep_template_variables: str
) -> None:
    email_var_names = [evn.strip() for evn in comma_sep_template_variables.split(",")]

    keys = (
        cosmos_db_session.execute(select(EmailTemplateKey.id).where(EmailTemplateKey.name.in_(email_var_names)))
        .scalars()
        .all()
    )

    email_template = cosmos_db_session.execute(
        select(EmailTemplate).where(
            EmailTemplate.template_id == template_id, EmailTemplate.retailer_id == retailer_config.id
        )
    ).scalar_one()

    for key in keys:
        required_key = EmailTemplateRequiredKey(email_template_id=email_template.id, email_template_key_id=key)
        cosmos_db_session.add(required_key)

    cosmos_db_session.commit()


# fmt: off
@given(parse("the retailer store name as: {store_name}"))
# fmt: on
def location_attached(cosmos_db_session: "Session", retailer_config: Retailer, store_name: str) -> None:
    retailer_store = RetailerStore(store_name=store_name, mid="1234", retailer_id=retailer_config.id)
    cosmos_db_session.add(retailer_store)
    cosmos_db_session.commit()


# fmt: off
@given(parse("the account has {reward_count} issued unexpired rewards for the {campaign_slug} "
             "campaign and {reward_slug} reward config"))
# fmt: on
def update_existing_account_holder_with_rewards(
    account_holder: AccountHolder,
    retailer_config: Retailer,
    reward_count: int,
    campaign_slug: str,
    cosmos_db_session: "Session",
    reward_slug: str,
) -> AccountHolder:

    create_rewards_for_existing_account_holder(
        cosmos_db_session,
        retailer_slug=retailer_config.slug,
        reward_count=reward_count,
        account_holder_id=account_holder.id,
        campaign_slug=campaign_slug,
        reward_slug=reward_slug,
    )

    return account_holder


# fmt: off
@given(parse("the account has {count} pending rewards for the {campaign_slug} campaign and {reward_slug} "
             "reward slug with value {reward_goal}"))
# fmt: on
def update_existing_account_holder_with_pending_rewards(
    account_holder: AccountHolder,
    retailer_config: Retailer,
    count: int,
    cosmos_db_session: "Session",
    reward_goal: int,
    campaign_slug: str,
    reward_slug: str,
) -> AccountHolder:
    create_pending_rewards_for_existing_account_holder(
        cosmos_db_session, count, account_holder.id, campaign_slug, reward_goal
    )

    return account_holder


# fmt: off
@given(parse("the account holder's {campaign_slug} balance is {amount:d}"))
# fmt: on
def update_existing_account_holder_with_campaign_balance(
    account_holder: AccountHolder, amount: int, cosmos_db_session: "Session", campaign_slug: str
) -> None:
    campaign = get_campaign_by_slug(cosmos_db_session=cosmos_db_session, campaign_slug=campaign_slug)
    cosmos_db_session.execute(
        update(CampaignBalance)
        .values(balance=amount)
        .where(
            CampaignBalance.account_holder_id == account_holder.id,
            CampaignBalance.campaign_id == campaign.id,
        )
    )

    cosmos_db_session.commit()
    logging.info(f"Account holder balance updated to {amount}")


# fmt: off
@then(parse("{expected_num_rewards:d} reward for the account holder shows as {reward_status} "
            "with redeemed date"))
# fmt: on
def verify_account_holder_reward_status(
    retailer_config: Retailer, account_holder: AccountHolder, expected_num_rewards: int, reward_status: str
) -> None:
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.ACCOUNTS_API_BASE_URL}{Endpoints.ACCOUNTS}"
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
    retailer_config: Retailer,
    reward_count: int,
    reward_slug: str,
    campaign_slug: str,
    cosmos_db_session: "Session",
) -> AccountHolder:
    create_rewards_for_existing_account_holder(
        cosmos_db_session,
        retailer_slug=retailer_config.slug,
        reward_count=reward_count,
        account_holder_id=account_holder.id,
        campaign_slug=campaign_slug,
        reward_slug=reward_slug,
    )
    return account_holder


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
    cosmos_db_session: "Session",
    retailer_config: Retailer,
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
    cosmos_db_session.add(campaign)
    cosmos_db_session.commit()

    return campaign


# fmt: off
@given(parse("the {campaign_slug} campaign has an earn rule with a threshold of {threshold:d}, an increment of {inc}, "
             "a multiplier of {mult:d} and max amount of {earn_max_amount:d}"))
# fmt: on
def create_earn_rule(
    cosmos_db_session: "Session",
    campaign_slug: str,
    threshold: int,
    inc: str,
    mult: int,
    earn_max_amount: int,
) -> None:
    converted_inc = None if inc == "None" else int(inc)
    campaign = cosmos_db_session.execute(select(Campaign).where(Campaign.slug == campaign_slug)).scalar_one()
    earn_rule = EarnRule(
        campaign_id=campaign.id,
        threshold=threshold,
        increment=converted_inc,
        increment_multiplier=mult,
        max_amount=earn_max_amount,
    )

    cosmos_db_session.add(earn_rule)
    cosmos_db_session.commit()


# fmt: off
@given(parse("the {campaign_slug} campaign has reward rule with reward goal: {reward_goal:d}, "
             "allocation window: {allocation_window} and reward cap: {reward_cap}"))
# fmt: on
def create_reward_rule(
    cosmos_db_session: "Session",
    campaign_slug: str,
    reward_goal: int,
    allocation_window: str,
    reward_cap: str,
    reward_config: Reward,
) -> None:
    campaign = get_campaign_by_slug(cosmos_db_session=cosmos_db_session, campaign_slug=campaign_slug)
    reward_goal = RewardRule(
        campaign_id=campaign.id,
        reward_goal=reward_goal,
        allocation_window=None if allocation_window == "None" else int(allocation_window),
        reward_cap=None if reward_cap == "None" else int(reward_cap),
        reward_config_id=reward_config.id,
    )
    cosmos_db_session.add(reward_goal)
    cosmos_db_session.commit()


@given(parse("BPL receives a transaction for the account holder for the amount of {amount} pennies"))
@when(parse("BPL receives a transaction for the account holder for the amount of {amount} pennies"))
def the_account_holder_transaction_request(
    account_holder: AccountHolder, retailer_config: Retailer, amount: int, request_context: dict
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
    retailer_config: Retailer,
    campaign_slug: str,
) -> None:
    payload: dict[str, Any] = {
        "requested_status": status,
        "campaign_slug": campaign_slug,
        "activity_metadata": {"sso_username": "qa_auto"},
    }

    request = send_post_campaign_status_change(
        request_context=request_context, retailer_slug=retailer_config.slug, request_body=payload
    )
    assert request.status_code == 200


# fmt: off
@when(parse("there are reward-issuance tasks for the account holders for the {reward_slug} reward slug "
            "and {campaign_slug} campaign_slug on the queue"))
# fmt: on
def enqueue_reward_issuance_tasks_for_account_holders(
    retailer_config: Retailer,
    cosmos_db_session: "Session",
    account_holders: list[AccountHolder],
    reward_slug: str,
    campaign_slug: str,
) -> None:
    reward_config_id = cosmos_db_session.execute(
        select(RewardConfig.id)
        .join(Retailer)
        .where(RewardConfig.slug == reward_slug, RewardConfig.retailer_id == retailer_config.id)
    ).scalar()

    campaign = get_campaign_by_slug(cosmos_db_session, campaign_slug)

    task_params_list = [
        {
            "campaign_id": campaign.id,
            "account_holder_id": ah.id,
            "reward_config_id": reward_config_id,
            "agent_state_params_raw": json.dumps(
                {
                    "associated_url": (
                        "http://dummy-reward-provider-site/reward"
                        f"?retailer={retailer_config.slug}&reward=a96c90cf-0944-44de-a180-bae2ed93816e"
                    )
                }
            ),
            "reason": "CAMPAIGN_END",
        }
        for ah in account_holders
    ]
    logging.info("Making reward-issuance tasks...")
    tasks = sync_create_many_tasks(cosmos_db_session, task_type_name="reward-issuance", params_list=task_params_list)
    cosmos_db_session.add_all(tasks)
    cosmos_db_session.commit()
    logging.info("Enqueueing reward-issuance tasks...")
    enqueue_many_retry_tasks(
        cosmos_db_session, retry_tasks_ids=[task.retry_task_id for task in tasks], connection=settings.redis
    )
