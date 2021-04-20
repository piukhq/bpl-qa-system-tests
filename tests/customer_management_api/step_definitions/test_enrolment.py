import json
import logging

from json import JSONDecodeError
from typing import TYPE_CHECKING

from pytest_bdd import given, parsers, scenarios, then, when

from tests.customer_management_api.api_requests.base import get_headers
from tests.customer_management_api.api_requests.enrolment import (
    send_invalid_post_enrolment,
    send_malformed_post_enrolment,
    send_post_enrolment,
)
from tests.customer_management_api.db_actions.account_holder import (
    assert_enrol_request_body_with_account_holder_profile_table,
    assert_enrol_request_body_with_account_holder_table,
    get_account_holder,
    get_account_holder_profile,
)
from tests.customer_management_api.db_actions.retailer import get_retailer
from tests.customer_management_api.payloads.enrolment import (
    all_required_and_all_optional_credentials,
    malformed_request_body,
    missing_credentials_request_body,
    missing_validation_request_body,
)
from tests.customer_management_api.response_fixtures.enrolment import EnrolResponses
from tests.customer_management_api.step_definitions.shared import check_response_status_code, enrol_account_holder

if TYPE_CHECKING:
    from requests import Response

scenarios("customer_management_api/enrolment/")

enrol_responses = EnrolResponses()


@given(parsers.parse("There is an existing account holder with the same email in the database for {retailer}"))
def post_enrolment_existing_account_holder(retailer: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer
    request_body = all_required_and_all_optional_credentials()
    resp = send_post_enrolment(retailer, request_body)
    assert resp.status_code == 202


@given(
    parsers.parse(
        "I previously enrolled a {retailer_slug} account holder " "passing in all required and all optional fields"
    )
)
@when(parsers.parse("I Enrol a {retailer_slug} account holder passing in all required and all optional fields"))
def post_enrolment(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context)


@when(parsers.parse("I Enrol a {retailer_slug} account holder with an malformed request"))
def post_malformed_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = malformed_request_body()
    resp = send_malformed_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"{resp.json()}, status code: {resp.status_code}")


@given(parsers.parse("I Enrol a {retailer_slug} account holder with an missing fields in request"))
def post_missing_credential_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = missing_credentials_request_body()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response: {resp.json()}, status code: {resp.status_code}")


@given(parsers.parse("I Enrol a {retailer_slug} account  holder and passing in fields will fail validation request"))
def post_missing_validation_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = missing_validation_request_body()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response: {resp.json()}, status code: {resp.status_code}")


@given(parsers.parse("I Enrol a {retailer_slug} account holder with an invalid token"))
def post_enrolment_invalid_token(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    resp = send_invalid_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response: {resp.json()}, status code: {resp.status_code}")
    assert resp.status_code == 401


@given(parsers.parse("I POST a {retailer_slug} account holder enrol request without a channel HTTP header"))
def post_no_channel_header(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    headers = get_headers()
    headers.pop("Bpl-User-Channel")
    resp = send_post_enrolment(retailer_slug, request_body, headers=headers)
    request_context["response"] = resp
    logging.info(f"Response: {resp.json()}, status code: {resp.status_code}")
    assert resp.status_code == 400


@when(
    parsers.parse("I Enrol a {retailer_slug} account holder " "passing in the same email as an existing account holder")
)
def post_enrolment_with_previous_request_details(retailer_slug: str, request_context: dict) -> None:
    existing_request_data = json.loads(request_context["response"].request.body)
    existing_email = existing_request_data["credentials"]["email"]

    new_request_body = all_required_and_all_optional_credentials()
    new_request_body["credentials"]["email"] = existing_email

    retailer_slug = request_context["retailer_slug"]
    resp = send_post_enrolment(retailer_slug, new_request_body)
    request_context["response"] = resp


@given(parsers.parse("the previous response returned a HTTP {status_code:d} status code"))
@then(parsers.parse("I receive a HTTP {status_code:d} status code in the response"))
def check_enrolment_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "Enrol")


@then(parsers.parse("I get a {response_fixture} enrol response body"))
def check_enrolment_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = enrol_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        f"POST Enrol Expected Response: {json.dumps(expected_response_body)} \n Actual Response: {resp.json()}"
    )
    assert resp.json() == expected_response_body


@then(parsers.parse("all fields I sent in the enrol request are saved in the database"))
def check_all_fields_saved_in_db(request_context: dict) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    retailer = get_retailer(retailer_slug)

    account_holder = get_account_holder(email, retailer)
    account_holder_id = account_holder.id
    account_holder_profile = get_account_holder_profile(account_holder_id)

    assert_enrol_request_body_with_account_holder_table(account_holder, request_body, retailer.id)
    assert_enrol_request_body_with_account_holder_profile_table(account_holder_profile, request_body)


@then(parsers.parse("the account holder is not saved in the database"))
def check_account_holder_is_not_saved_in_db(request_context: dict) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    account_holder = get_account_holder(email, retailer_slug)
    assert account_holder is None


def response_to_json(response: "Response") -> dict:
    try:
        response_json = response.json()
    except JSONDecodeError or Exception:
        raise Exception(f"Empty response and the response Status Code is {str(response.status_code)}")
    return response_json
