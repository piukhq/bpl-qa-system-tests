import json
import logging

from typing import TYPE_CHECKING

from deepdiff import DeepDiff
from pytest_bdd import given, parsers, scenarios, then, when

from tests.customer_management_api.api_requests.getbycredentials import (
    send_invalid_post_getbycredentials,
    send_malformed_post_getbycredentials,
    send_post_getbycredentials,
)
from tests.customer_management_api.db_actions.account_holder import get_account_holder, get_active_account_holder
from tests.customer_management_api.db_actions.retailer import get_retailer
from tests.customer_management_api.payloads.getbycrdentials import (
    all_required_credentials,
    malformed_request_body,
    missing_credentials_request_body,
    non_existent_user_credentials,
    wrong_validation_request_body,
)
from tests.customer_management_api.response_fixtures.getbycredentials import GetByCredentialsResponses
from tests.customer_management_api.response_fixtures.shared import account_holder_details_response_body
from tests.customer_management_api.step_definitions.shared import (
    check_response_status_code,
    enrol_account_holder,
    non_existent_account_holder,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

scenarios("customer_management_api/getbycredentials/")

getbycredentials_responses = GetByCredentialsResponses()


@given(parsers.parse("I previously successfully enrolled a {retailer_slug} account holder"))
def setup_account_holder(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context)


@given(parsers.parse("I received a HTTP {status_code:d} status code response"))
def setup_check_enrolment_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "Enrol")


@then(parsers.parse("I get a {response_fixture} enrol response body"))
def check_enrolment_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = getbycredentials_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        "POST enrol expected response: {} \n actual response: {}".format(
            json.dumps(expected_response_body), resp.json()
        )
    )
    assert resp.json() == expected_response_body


@then("I get a success getbycredentials response body")
def check_successful_getbycredentials_response(db_session: "Session", request_context: dict) -> None:
    expected_response_body = account_holder_details_response_body(db_session, request_context["account_holder"].id)
    resp = request_context["response"]
    logging.info(
        "POST getbycredentials expected response: {} \n actual response: {}".format(
            json.dumps(expected_response_body), resp.json()
        )
    )
    diff = DeepDiff(resp.json(), expected_response_body, significant_digits=2, ignore_numeric_type_changes=True)
    assert not diff


@when(parsers.parse("I post getbycredentials a {retailer_slug} account holder passing in all required credentials"))
def post_getbycredentials(db_session: "Session", retailer_slug: str, request_context: dict) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    retailer = get_retailer(db_session, retailer_slug)

    if request_context.get("account_holder_exists", True):
        account_holder = get_account_holder(db_session, email, retailer)
        request_context["account_holder"] = account_holder
        request_body = all_required_credentials(account_holder)
    else:
        request_body = non_existent_user_credentials(email, retailer.account_number_prefix)

    request_context["retailer_slug"] = retailer_slug
    resp = send_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"{resp.json()}, status code: {resp.status_code}")


@when("I post getbycredentials an invalid-retailer's account holder passing in all required credentials")
def post_getbycredentials_invalid_retailer(request_context: dict) -> None:
    request_body = all_required_credentials()
    request_context["retailer_slug"] = "invalid-retailer"
    resp = send_post_getbycredentials("invalid-retailer", request_body)
    request_context["response"] = resp
    logging.info(f"{resp.json()}, status code: {resp.status_code}")


@when(parsers.parse("I getbycredentials a {retailer_slug} account holder with an malformed request"))
def post_malformed_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = malformed_request_body()
    resp = send_malformed_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"{resp.json()}, status code: {resp.status_code}")


@when(parsers.parse("I getbycredentials a {retailer_slug} account holder with a missing field in the request"))
def post_missing_field_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = missing_credentials_request_body()
    resp = send_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"{resp.json()}, status code: {resp.status_code}")


@when(parsers.parse("I getbycredentials a {retailer_slug} account holder passing in fields that will fail validation"))
def post_wrong_validation_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = wrong_validation_request_body()
    resp = send_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"{resp.json()}, status code: {resp.status_code}")


@when(parsers.parse("I getbycredentials a {retailer_slug} account holder with an invalid authorisation token"))
def post_invalid_token_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_credentials()
    resp = send_invalid_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"{resp.json()}, status code: {resp.status_code}")


@given(parsers.parse("the enrolled account holder has been activated"))
def check_account_holder_is_active(db_session: "Session", request_context: dict) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]

    account_holder = get_active_account_holder(db_session, email, retailer_slug)

    assert account_holder.status == "ACTIVE"
    assert account_holder.account_number is not None


@then(parsers.parse("I receive a HTTP {status_code:d} status code in the getbycredentials response"))
def check_getbycredentials_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "getbycredentials")


@given(parsers.parse("The {retailer_slug}'s account holder I want to retrieve does not exists"))
def non_existent_getbycredentials_account_holder(retailer_slug: str, request_context: dict) -> None:
    non_existent_account_holder(retailer_slug, request_context)


@then(parsers.parse("I get a {response_fixture} getbycredentials response body"))
def check_getbycredentials_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = getbycredentials_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        "POST getbycredentials expected response: %s \n actual response: %s"
        % (json.dumps(expected_response_body), resp.json())
    )
    assert resp.json() == expected_response_body
