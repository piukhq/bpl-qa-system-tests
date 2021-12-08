import json
import logging
import time
import uuid

from typing import TYPE_CHECKING, Optional

from pytest_bdd import given, when
from pytest_bdd.parsers import parse
from sqlalchemy.future import select

from db.polaris.models import AccountHolderCampaignBalance
from tests.customer_management_api.api_requests.accounts import send_get_accounts
from tests.customer_management_api.api_requests.base import get_headers
from tests.customer_management_api.api_requests.enrolment import send_post_enrolment
from tests.customer_management_api.db_actions.account_holder import get_active_account_holder
from tests.customer_management_api.payloads.enrolment import (
    all_required_and_all_optional_credentials,
    only_required_credentials,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@given(parse("I previously successfully enrolled a {retailer_slug} account holder"))
@when(parse("I Enrol a {retailer_slug} account holder passing in all required and all optional fields"))
def enrol_account_holder_with_all_fields(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context)


def enrol_account_holder(
    retailer_slug: str,
    request_context: dict,
    incl_optional_fields: bool = True,
    callback_url: Optional[str] = None,
) -> None:
    request_context["retailer_slug"] = retailer_slug
    if incl_optional_fields:
        request_body = all_required_and_all_optional_credentials(callback_url=callback_url)
    else:
        request_body = only_required_credentials()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp


@given(parse("The {retailer_slug} account holder I want to retrieve does not exists"))
def non_existent_account_holder(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_context["account_holder_exists"] = False

    class UnsentRequest:
        body = json.dumps(all_required_and_all_optional_credentials())

    class FakeResponse:
        status = 202
        request = UnsentRequest

    request_context["response"] = FakeResponse


def enrol_missing_channel_header(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    headers = get_headers()
    headers.pop("bpl-user-channel")
    resp = send_post_enrolment(retailer_slug, request_body, headers=headers)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")
    assert resp.status_code == 400


def enrol_missing_third_party_identifier(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    request_body.pop("third_party_identifier")
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")
    assert resp.status_code == 422


@given("the enrolled account holder has been activated and i know its current balances")
@given("the enrolled account holder has been activated")
def check_account_holder_is_active(polaris_db_session: "Session", request_context: dict) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]

    account_holder = get_active_account_holder(polaris_db_session, email, retailer_slug)
    for i in range(1, 5):
        time.sleep(i)
        polaris_db_session.refresh(account_holder)
        if account_holder.status != "PENDING":
            break

    assert account_holder.status == "ACTIVE"
    assert account_holder.account_number is not None

    request_context["account_holder"] = account_holder
    request_context["balance"] = (
        polaris_db_session.execute(
            select(AccountHolderCampaignBalance).where(
                AccountHolderCampaignBalance.account_holder_id == str(account_holder.id),
                AccountHolderCampaignBalance.campaign_slug == "test-campaign-1",
            )
        )
        .scalars()
        .first()
    )


@when("I send a get /accounts request for the account holder by UUID")
def get_account(request_context: dict) -> None:
    account_holder = request_context.get("account_holder", None)

    if account_holder is not None:
        account_holder_id = str(account_holder.id)
    else:
        account_holder_id = str(uuid.uuid4())

    resp = send_get_accounts(request_context["retailer_slug"], account_holder_id)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")
