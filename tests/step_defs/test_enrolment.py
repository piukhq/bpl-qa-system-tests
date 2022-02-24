import json
import logging
from time import sleep
from uuid import uuid4

from faker import Faker
from pytest_bdd import scenarios, then, when
from pytest_bdd.parsers import parse

import settings
from db.carina.models import RewardConfig
from db.polaris.models import RetailerConfig, AccountHolder
from db.vela.models import Campaign

from typing import TYPE_CHECKING, Optional

from settings import MOCK_SERVICE_BASE_URL
from tests.db_actions.account_holder import get_account_holder
from tests.db_actions.retry_tasks import get_latest_callback_task_for_account_holder
from tests.requests.enrolment import send_post_enrolment

scenarios("../features")

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

fake = Faker(locale="en_GB")


@then("Retailer, Campaigns, and RewardConfigs are successfully created in the database")
def enrolment(
    retailer_config: RetailerConfig, standard_campaigns: list[Campaign], standard_reward_configs: list[RewardConfig]
) -> None:
    assert retailer_config is not None
    assert standard_campaigns
    assert standard_reward_configs


@when(parse("I Enrol a {retailer_slug} account holder passing in all required and all optional fields"))
def enorl_accountholder_with_all_required_fields(retailer_config: RetailerConfig, request_context: dict) -> None:
    enrol_account_holder(retailer_config, request_context)


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
    # phone_prefix = "0" if random.randint(0, 1) else "+44"
    # address = fake.street_address().split("\n")
    # address_1 = address[0]
    # if len(address) > 1:
    #     address_2 = address[1]
    # else:
    #     address_2 = fake.street_name()

    return {
        "email": f"qa_pytest{uuid4()}@bink.com",
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
    return get_account_holder(polaris_db_session, email)


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
