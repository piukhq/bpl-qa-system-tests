import json
import logging
import uuid

from typing import TYPE_CHECKING

from deepdiff import DeepDiff
from pytest_bdd import given, parsers, scenarios, then, when

from tests.customer_management_api.api_requests.accounts import (
    send_get_accounts,
    send_get_accounts_status,
    send_invalid_get_accounts,
    send_invalid_get_accounts_status,
    send_malformed_get_accounts,
)
from tests.customer_management_api.api_requests.base import get_headers
from tests.customer_management_api.db_actions.account_holder import get_account_holder
from tests.customer_management_api.db_actions.retailer import get_retailer
from tests.customer_management_api.response_fixtures.accounts import AccountsResponses
from tests.customer_management_api.response_fixtures.shared import (
    account_holder_details_response_body,
    account_holder_status_response_body,
)
from tests.customer_management_api.step_definitions.shared import (
    check_response_status_code,
    enrol_account_holder,
    non_existent_account_holder,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

scenarios("customer_management_api/accounts/")
accounts_responses = AccountsResponses()


@given(parsers.parse("I previously successfully enrolled a {retailer_slug} account holder"))
def setup_account_holder(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context)


@given(parsers.parse("I received a HTTP {status_code:d} status code response"))
def setup_check_enrolment_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "Enrol")


@when(parsers.parse("I send a get /accounts request for a {retailer_slug} account holder by UUID"))
def get_account(db_session: "Session", retailer_slug: str, request_context: dict) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    retailer = get_retailer(db_session, retailer_slug)

    if request_context.get("account_holder_exists", True):
        account_holder = get_account_holder(db_session, email, retailer)
        assert account_holder is not None
        request_context["account_holder"] = account_holder
        account_holder_id = account_holder.id
    else:
        account_holder_id = uuid.uuid4()

    resp = send_get_accounts(retailer_slug, str(account_holder_id))
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when(parsers.parse("I send a get /accounts request for a {retailer_slug} account holder status by UUID"))
def get_account_status(db_session: "Session", retailer_slug: str, request_context: dict) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    retailer = get_retailer(db_session, retailer_slug)

    if request_context.get("account_holder_exists", True):
        account_holder = get_account_holder(db_session, email, retailer)
        assert account_holder is not None
        request_context["account_holder"] = account_holder
        account_holder_id = account_holder.id
    else:
        account_holder_id = uuid.uuid4()

    resp = send_get_accounts_status(retailer_slug, str(account_holder_id))
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@then(parsers.parse("I receive a HTTP {status_code:d} status code in the accounts response"))
def check_getbycredentials_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "accounts")


@then("I get a success accounts response body")
def check_successful_accounts_response(db_session: "Session", request_context: dict) -> None:
    expected_response_body = account_holder_details_response_body(db_session, request_context["account_holder"].id)
    resp = request_context["response"]
    logging.info(
        f"GET accounts expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"GET accounts actual response: {json.dumps(resp.json(), indent=4)}"
    )
    diff = DeepDiff(resp.json(), expected_response_body, significant_digits=2)
    assert not diff


@then("I get a success accounts status response body")
def check_successful_accounts_status_response(db_session: "Session", request_context: dict) -> None:
    expected_response_body = account_holder_status_response_body(db_session, request_context["account_holder"].id)
    resp = request_context["response"]
    logging.info(
        f"GET accounts expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"GET accounts actual response: {json.dumps(resp.json(), indent=4)}"
    )
    diff = DeepDiff(resp.json(), expected_response_body, significant_digits=2)
    assert not diff


@then(parsers.parse("I get a {response_fixture} accounts response body"))
def check_accounts_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = accounts_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        f"POST getbycredentials expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST getbycredentials actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body


@when(
    parsers.parse(
        "I send a get /accounts request for a {retailer_slug} account holder by UUID "
        "with an invalid authorisation token"
    )
)
def get_invalid_token_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    resp = send_invalid_get_accounts(retailer_slug, str(uuid.uuid4()))
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when(
    parsers.parse(
        "I send a get /accounts request for a {retailer_slug} account holder status by UUID "
        "with an invalid authorisation token"
    )
)
def get_accounts_status_invalid_token_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    resp = send_invalid_get_accounts_status(retailer_slug, str(uuid.uuid4()))
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when(
    parsers.parse(
        "I send a get /accounts request for a {retailer_slug} account holder by UUID without a channel header"
    )
)
def get_missing_channel_header_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    headers = get_headers()
    del headers["bpl-user-channel"]
    resp = send_get_accounts(retailer_slug, str(uuid.uuid4()), headers=headers)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when(
    parsers.parse("I send a get /accounts request for a {retailer_slug} account holder by UUID with a malformed UUID")
)
def get_malformed_uuid_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    resp = send_malformed_get_accounts(retailer_slug)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when("I send a get /accounts request for an invalid-retailer account holder by UUID")
def get_account_invalid_retailer(request_context: dict) -> None:
    request_context["retailer_slug"] = "invalid-retailer"
    resp = send_get_accounts("invalid-retailer", str(uuid.uuid4()))
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when("I send a get /accounts request for an invalid-retailer account holder status by UUID")
def get_accounts_status_invalid_retailer(request_context: dict) -> None:
    request_context["retailer_slug"] = "invalid-retailer"
    resp = send_get_accounts_status("invalid-retailer", str(uuid.uuid4()))
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@given(parsers.parse("The {retailer_slug}'s account holder I want to retrieve does not exists"))
def non_existent_accounts_account_holder(retailer_slug: str, request_context: dict) -> None:
    non_existent_account_holder(retailer_slug, request_context)
