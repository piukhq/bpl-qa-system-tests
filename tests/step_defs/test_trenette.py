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

import settings

from db.carina.models import RewardConfig
from db.polaris.models import AccountHolder, RetailerConfig
from db.vela.models import Campaign
from settings import MOCK_SERVICE_BASE_URL
from tests.db_actions.polaris import get_account_holder
from tests.db_actions.retry_tasks import get_latest_callback_task_for_account_holder
from tests.db_actions.vela import get_reward_adjustment_task_status
from tests.requests.enrolment import send_post_enrolment
from tests.requests.status_change import send_post_campaign_status_change
from tests.requests.transaction import post_transaction_request
from tests.shared_utils.fixture_loader import load_fixture
from tests.shared_utils.response_fixtures.errors import TransactionResponses

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


@when(parse("i Enrol a account holder passing in all required and all optional fields"))
@when(parse("the account holder enrol to retailer with all required and all optional fields"))
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


@then(parse("i receive a HTTP {status_code:d} status code response"))
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


@when(parse("the account holder POST transaction request for {retailer_slug} retailer with {amount:d}"))
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


@then(parse("BPL responds with a HTTP {status_code:d} and {response_type} message"))
def the_account_holder_get_response(status_code: int, response_type: str, request_context: dict) -> None:
    assert request_context["resp"].status_code == status_code
    assert request_context["resp"].json() == TransactionResponses.get_json(response_type)


@then(parse("the account holder's {campaign_slug} accumulator campaign balance {transaction_amount:d} is updated"))
def check_account_holder_accumulator_campaign_balance_is_updated(
    account_holder: AccountHolder,
    retailer_config: RetailerConfig,
    campaign_slug: str,
    polaris_db_session: "Session",
    vela_db_session: "Session",
    transaction_amount: int,
) -> None:
    polaris_db_session.refresh(account_holder)
    fixture_data = load_fixture(retailer_config.slug)
    account_holder_campaign_balances = account_holder.accountholdercampaignbalance_collection
    # campaign_info_by_slug = {info['slug']: info for info in fixture_data.campaign}
    earn_rule_increment_multiplier = fixture_data.earn_rule[campaign_slug][0]["increment_multiplier"]
    reward_goal = fixture_data.reward_rule[campaign_slug][0]["reward_goal"]
    balances_by_slug = {ahcb.campaign_slug: ahcb for ahcb in account_holder_campaign_balances}

    expected_balance = transaction_amount * earn_rule_increment_multiplier
    if expected_balance >= reward_goal:
        expected_balance -= reward_goal
    logging.info(f"Expected Balance : {expected_balance}")

    for i in range(5):
        sleep(i)
        polaris_db_session.refresh(balances_by_slug[campaign_slug])

        if balances_by_slug[campaign_slug].balance == expected_balance:
            break

    logging.info(f"Account holder campaign balance : {balances_by_slug[campaign_slug].balance}")

    assert balances_by_slug[campaign_slug].balance == expected_balance


@then(parse("the account holder {issued} reward"))
def issued_reward(issued: str, get_account_response_by_uuid: "Response") -> None:
    assert get_account_response_by_uuid is not None
    assert issued == get_account_response_by_uuid.json()["rewards"][0]["status"]


@then(parse("status {status} appeared"))
def status_code_appeared(status: str, get_account_response_by_uuid: "Response") -> None:
    assert status == get_account_response_by_uuid.json()["status"]


@then("the account holder's balance got adjusted")
def the_account_holder_balance_got_adjusted(request_context: dict, get_account_response_by_uuid: "Response") -> None:
    assert (
        request_context["account_holder_campaign_balance"].balance
        == get_account_response_by_uuid.json()["current_balances"][0]["value"]
    )


@then("the account holder's UUID and account number appearing correct")
def verify_uuid_and_account(request_context: dict, get_account_response_by_uuid: "Response") -> None:
    assert request_context["account_holder_uuid"] == get_account_response_by_uuid.json()["UUID"]
    assert request_context["account_number"] == get_account_response_by_uuid.json()["account_number"]


@then(parse("the status is then changed to {status} for {campaign_slug} for the retailer {retailer_slug}"))
def send_post_campaign_change_request(status: str, retailer_slug: str, campaign_slug: str) -> None:
    payload = {
        "requested_status": status,
        "campaign_slugs": [campaign_slug],
    }

    request = send_post_campaign_status_change(retailer_slug=retailer_slug, request_body=payload)
    assert request.status_code == 200


@then(parse("the account holder's {campaign_slug} balance no longer exists"))
def check_account_holder_balance_is_updated(
    campaign_slug: str,
    polaris_db_session: "Session",
    account_holder: AccountHolder,
) -> None:
    for i in range(5):
        sleep(i)
        polaris_db_session.refresh(account_holder)
        account_holder_campaign_balance = [
            x for x in account_holder.accountholdercampaignbalance_collection if x.campaign_slug == campaign_slug
        ]
        if not account_holder_campaign_balance:
            break
    assert not account_holder_campaign_balance


@then(parse("the reward adjustment retry task for {campaign_slug} has a status of {status}"))
def check_reward_adjustment_task_status_is_failed(
    vela_db_session: "Session",
    campaign_slug: str,
    status: str,
) -> None:
    resp = get_reward_adjustment_task_status(vela_db_session, campaign_slug)
    assert resp == status


def _get_reward_slug_from_account_holder_reward_collection(
    account_holder: AccountHolder,
    reward_slug: str,
) -> list:
    return [x for x in account_holder.accountholderreward_collection if x.reward_slug == reward_slug]


@then(parse("the {retailer_slug} account is {issued} reward {reward_slug}"))
def check_reward_issuance(
    reward_slug: str,
    issued: str,
    account_holder: AccountHolder,
    polaris_db_session: "Session",
) -> None:
    if issued == "not issued":
        for i in range(5):
            sleep(i)
            polaris_db_session.refresh(account_holder)
            account_holder_reward = _get_reward_slug_from_account_holder_reward_collection(account_holder, reward_slug)
            if not account_holder_reward:
                break
        assert not account_holder_reward
    elif issued == "issued":
        for i in range(5):
            sleep(i)
            polaris_db_session.refresh(account_holder)
            account_holder_reward = _get_reward_slug_from_account_holder_reward_collection(account_holder, reward_slug)
            if account_holder_reward:
                break
        assert account_holder_reward
    else:
        raise ValueError(f"{issued} is not an acceptable value")
