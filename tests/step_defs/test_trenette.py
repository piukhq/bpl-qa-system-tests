import json
import logging
import time
import uuid

from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from faker import Faker
from pytest_bdd import scenarios, then, when
from pytest_bdd.parsers import parse
from sqlalchemy.future import select

import settings

from db.carina.models import RewardConfig
from db.polaris.models import AccountHolder, RetailerConfig
from db.vela.models import Campaign
from settings import MOCK_SERVICE_BASE_URL
from tests.api.base import Endpoints
from tests.db_actions.polaris import get_account_holder
from tests.db_actions.retry_tasks import get_latest_callback_task_for_account_holder
from tests.requests.enrolment import send_get_accounts, send_post_enrolment
from tests.requests.transaction import post_transaction_request
from tests.shared_utils.fixture_loader import load_fixture
from tests.shared_utils.response_fixtures.errors import TransactionResponses
from tests.shared_utils.shared_steps import fetch_balance_for_account_holder

scenarios("../features/trenette")

if TYPE_CHECKING:
    from requests import Response
    from sqlalchemy.orm import Session

fake = Faker(locale="en_GB")


@then("Retailer, Campaigns, and RewardConfigs are successfully created in the database")
def enrolment(
    retailer_config: RetailerConfig, standard_campaigns: list[Campaign], standard_reward_configs: list[RewardConfig]
) -> None:
    assert retailer_config is not None
    assert standard_campaigns
    assert standard_reward_configs


@when(parse("I Enrol a account holder passing in all required and all optional fields"))
@when(parse("The account holder enrol to retailer with all required and all optional fields"))
def enrol_accountholder_with_all_required_fields(
    retailer_config: RetailerConfig, request_context: dict, polaris_db_session: "Session"
) -> None:
    return enrol_account_holder(retailer_config, request_context)


def enrol_account_holder(
    retailer_config: RetailerConfig,
    request_context: dict,
    incl_optional_fields: bool = True,
    callback_url: Optional[str] = None,
) -> None:
    request_context["retailer_slug"] = retailer_config.slug
    if incl_optional_fields:
        request_body = all_required_and_all_optional_credentials(callback_url=callback_url)
    else:
        request_body = only_required_credentials()

    resp = send_post_enrolment(request_context["retailer_slug"], request_body)
    time.sleep(3)
    request_context["email"] = request_body["credentials"]["email"]
    request_context["response"] = resp
    request_context["status_code"] = resp.status_code
    logging.info(f"Response : {request_context}")


def all_required_and_all_optional_credentials(callback_url: Optional[str] = None) -> dict:
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


@then("the account holder is activated")
def account_holder_is_activated(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder, "account holder not found from request_context"
    for i in range(1, 18):  # 3 minute wait
        logging.info(
            f"Sleeping for 10 seconds while waiting for account activation (account holder id: {account_holder.id})..."
        )
        sleep(3)
        polaris_db_session.refresh(account_holder)
        if account_holder.status == "ACTIVE":
            break
    assert account_holder.status == "ACTIVE"
    assert account_holder.account_number is not None
    assert account_holder.account_holder_uuid is not None
    assert account_holder.opt_out_token is not None


def get_account_holder_from_request_data(
    polaris_db_session: "Session", request_context: dict
) -> Optional[AccountHolder]:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer = polaris_db_session.query(RetailerConfig).filter_by(slug=request_context["retailer_slug"]).first()
    return get_account_holder(polaris_db_session, email, retailer.id)


@then(parse("I receive a HTTP {status_code:d} status code response"))
def check_response_status_code(status_code: int, request_context: dict) -> None:
    resp = request_context["response"]
    logging.info(f"Response HTTP status code: {resp.status_code} Response status: {json.dumps(resp.json(), indent=4)}")
    assert resp.status_code == status_code


@then("an enrolment callback task is saved in the database")
def verify_callback_task_saved_in_db(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    callback_task = get_latest_callback_task_for_account_holder(polaris_db_session, account_holder.account_holder_uuid)
    assert callback_task is not None
    assert settings.MOCK_SERVICE_BASE_URL in callback_task.get_params()["callback_url"]
    assert callback_task.get_params()["third_party_identifier"] == "identifier"
    assert callback_task.get_params()["account_holder_uuid"] == str(account_holder.account_holder_uuid)


@when(parse("The account holder POST transaction request for {retailer_slug} retailer with {amount:d}"))
def the_account_holder_transaction_request(retailer_slug: str, amount: int, request_context: dict) -> None:
    account_holder_uuid = request_context["account_holder_uuid"]

    payload = {
        "id": str(uuid.uuid4()),
        "transaction_total": amount,
        "datetime": int(datetime.utcnow().timestamp()),
        "MID": "12432432",
        "loyalty_id": str(account_holder_uuid),
    }
    logging.info(f"Payload of transaction : {json.dumps(payload)}")
    post_transaction_request(payload, retailer_slug, request_context)


@when(parse("An {status} account holder exists for {retailer_slug}"))
def setup_account_holder(
    status: str,
    retailer_slug: str,
    request_context: dict,
    polaris_db_session: "Session",
    standard_campaigns: list[Campaign],
) -> None:
    email = request_context["email"]
    retailer = polaris_db_session.query(RetailerConfig).filter_by(slug=retailer_slug).first()
    if retailer is None:
        raise ValueError(f"a retailer with slug '{retailer_slug}' was not found in the db.")

    account_status = {"active": "ACTIVE"}.get(status, "PENDING")
    if "campaign" in request_context:
        campaign_slug = request_context["campaign"].slug
    else:
        campaign_slug = standard_campaigns[0].slug

    account_holder = (
        polaris_db_session.execute(
            select(AccountHolder).where(AccountHolder.email == email, AccountHolder.retailer_id == retailer.id)
        )
        .scalars()
        .first()
    )

    account_holder.status = account_status

    account_holder_campaign_balance = fetch_balance_for_account_holder(
        polaris_db_session, account_holder, campaign_slug
    )

    request_context["campaign_slug"] = campaign_slug
    request_context["account_holder_uuid"] = str(account_holder.account_holder_uuid)
    request_context["account_number"] = account_holder.account_number
    request_context["account_holder"] = account_holder
    request_context["retailer_id"] = retailer.id
    request_context["retailer_slug"] = retailer.slug
    request_context["start_balance"] = 0
    request_context["account_holder_campaign_balance"] = account_holder_campaign_balance

    logging.info(f"Active account holder uuid:{account_holder.account_holder_uuid}\n" f"Retailer slug: {retailer_slug}")


@then(parse("The account holder get a HTTP {status_code:d} with {response_type} response"))
def the_account_holder_get_response(status_code: int, response_type: str, request_context: dict) -> None:
    assert request_context["resp"].status_code == status_code
    assert request_context["resp"].json() == TransactionResponses.get_json(response_type)


@then("The account holder's balance is updated")
def check_account_holder_balance_is_updated(
    request_context: dict, polaris_db_session: "Session", vela_db_session: "Session"
) -> None:
    fixture_data = load_fixture(request_context["retailer_slug"])
    account_holder_campaign_balance = request_context["account_holder_campaign_balance"]
    earn_rule_increment = fixture_data.earn_rule[request_context["campaign_slug"]][0]["increment"]
    earn_rule_increment_multiplier = fixture_data.earn_rule[request_context["campaign_slug"]][0]["increment_multiplier"]
    reward_goal = fixture_data.reward_rule[request_context["campaign_slug"]][0]["reward_goal"]

    expected_balance = account_holder_campaign_balance.balance + (earn_rule_increment * earn_rule_increment_multiplier)
    if expected_balance >= reward_goal:
        expected_balance -= reward_goal
    logging.info(f"Expected Balance : {expected_balance}")

    for i in range(5):
        sleep(i)
        polaris_db_session.refresh(account_holder_campaign_balance)

        if account_holder_campaign_balance.balance == expected_balance:
            break

    logging.info(f"Account holder campaign balance : {account_holder_campaign_balance.balance}")

    assert account_holder_campaign_balance.balance == expected_balance
    request_context["account_holder_campaign_balance"] = account_holder_campaign_balance


@when("The account holder send GET accounts request by UUID", target_fixture="get_account_response_by_uuid")
def send_get_request_to_account_holder(request_context: dict) -> "Response":
    time.sleep(3)
    resp = send_get_accounts(request_context["retailer_slug"], request_context["account_holder_uuid"])
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET{settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{request_context['account_holder_uuid']}: {json.dumps(resp.json(), indent=4)}"
    )
    return resp


@then(parse("The account holder {issued} reward"))
def issued_reward(issued: str, get_account_response_by_uuid: "Response") -> None:
    assert get_account_response_by_uuid is not None
    assert issued == get_account_response_by_uuid.json()["rewards"][0]["status"]


@then(parse("status {status} appeared"))
def status_code_appeared(status: str, get_account_response_by_uuid: "Response") -> None:
    assert status == get_account_response_by_uuid.json()["status"]


@then("The account holder's balance got adjusted")
def the_account_holder_balance_got_adjusted(request_context: dict, get_account_response_by_uuid: "Response") -> None:
    assert (
        request_context["account_holder_campaign_balance"].balance
        == get_account_response_by_uuid.json()["current_balances"][0]["value"]
    )


@then("The account holder's UUID and account number appearing correct")
def verify_uuid_and_account(request_context: dict, get_account_response_by_uuid: "Response") -> None:
    assert request_context["account_holder_uuid"] == get_account_response_by_uuid.json()["UUID"]
    assert request_context["account_number"] == get_account_response_by_uuid.json()["account_number"]
