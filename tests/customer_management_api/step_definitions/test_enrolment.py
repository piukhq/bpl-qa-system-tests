import json
import logging

from json import JSONDecodeError
from time import sleep
from typing import TYPE_CHECKING, Optional

from pytest_bdd import given, parsers, scenarios, then, when

import settings

from db.polaris.models import AccountHolder, AccountHolderActivation
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
from tests.customer_management_api.db_actions.account_holder_activation import get_account_holder_activation
from tests.customer_management_api.db_actions.retailer import get_retailer
from tests.customer_management_api.payloads.enrolment import (
    all_required_and_all_optional_credentials,
    bad_field_validation_request_body,
    malformed_request_body,
    missing_credentials_request_body,
)
from tests.customer_management_api.response_fixtures.enrolment import EnrolResponses
from tests.customer_management_api.step_definitions.shared import (
    check_response_status_code,
    enrol_account_holder,
    enrol_missing_channel_header,
    enrol_missing_third_party_identifier,
)

if TYPE_CHECKING:
    from requests import Response
    from sqlalchemy.orm import Session

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


@when(
    parsers.parse(
        "I Enrol a {retailer_slug} account holder passing in all required and all optional fields with a "
        "callback URL known to produce an HTTP {status_code:d} response"
    )
)
def post_enrolment_with_known_callback_side_effect(retailer_slug: str, status_code: int, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context, callback_url=get_callback_url(status_code=status_code))


@when(
    parsers.parse(
        "I Enrol a {retailer_slug} account holder passing in all required and all optional fields with a "
        "callback URL known to produce {num_failures:d} consecutive HTTP {status_code:d} responses"
    )
)
def post_enrolment_with_known_repeated_callback_side_effect(
    retailer_slug: str, num_failures: int, status_code: int, request_context: dict
) -> None:
    enrol_account_holder(
        retailer_slug,
        request_context,
        callback_url=get_callback_url(status_code=status_code, num_failures=num_failures),
    )


@when(
    parsers.parse(
        "I Enrol a {retailer_slug} account holder passing in all required and all optional fields with a "
        "callback URL known to timeout after {timeout_secs:d} seconds"
    )
)
def post_enrolment_with_known_callback_timeout(retailer_slug: str, timeout_secs: int, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context, callback_url=get_callback_url(timeout_seconds=timeout_secs))


@when(parsers.parse("I Enrol a {retailer_slug} account holder passing in only required fields"))
def post_enrolment_only_required_fields(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context, incl_optional_fields=False)


@when(parsers.parse("I Enrol a {retailer_slug} account holder with an malformed request"))
def post_malformed_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = malformed_request_body()
    resp = send_malformed_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@given(parsers.parse("I Enrol a {retailer_slug} account holder with an missing fields in request"))
def post_missing_credential_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = missing_credentials_request_body()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response: {resp.json()}, status code: {resp.status_code}")


@given(parsers.parse("I Enrol a {retailer_slug} account holder and passing in fields will fail validation request"))
def post_enrolment_with_wrongly_formatted_values(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = bad_field_validation_request_body()
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
    enrol_missing_channel_header(retailer_slug, request_context)


@given(
    parsers.parse(
        "I POST a {retailer_slug} account holder enrol request omitting third_party_identifier from the request body"
    )
)
def post_no_third_party_identifier(retailer_slug: str, request_context: dict) -> None:
    enrol_missing_third_party_identifier(retailer_slug, request_context)


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
        f"POST enrol expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST enrol actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body


@then(parsers.parse("all fields I sent in the enrol request are saved in the database"))
def check_all_fields_saved_in_db(polaris_db_session: "Session", request_context: dict) -> None:
    polaris_db_session.expire_all()
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    retailer = get_retailer(polaris_db_session, retailer_slug)

    account_holder = get_account_holder(polaris_db_session, email, retailer)
    assert account_holder is not None
    account_holder_profile = get_account_holder_profile(polaris_db_session, str(account_holder.id))
    assert_enrol_request_body_with_account_holder_table(account_holder, request_body, retailer.id)
    assert_enrol_request_body_with_account_holder_profile_table(account_holder_profile, request_body)


def get_account_holder_from_request_data(
    polaris_db_session: "Session", request_context: dict
) -> Optional[AccountHolder]:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    return get_account_holder(polaris_db_session, email, retailer_slug)


@then(parsers.parse("the account holder is not saved in the database"))
def check_account_holder_is_not_saved_in_db(polaris_db_session: "Session", request_context: dict) -> None:
    assert get_account_holder_from_request_data(polaris_db_session, request_context) is None


@then(parsers.parse("the account holder is saved in the database"))
def check_account_holder_is_saved_in_db(polaris_db_session: "Session", request_context: dict) -> None:
    assert get_account_holder_from_request_data(polaris_db_session, request_context) is not None


@then(parsers.parse("an account holder activation is saved in the database"))
def check_account_holder_activation_is_saved_in_db(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    activation = get_account_holder_activation(polaris_db_session, account_holder.id)
    assert activation is not None
    assert settings.MOCK_SERVICE_BASE_URL in activation.callback_url
    assert activation.third_party_identifier == "identifier"


@then(parsers.parse("the enrolment callback is tried"))
def check_enrolment_callback_is_tried(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    activation = get_account_holder_activation(polaris_db_session, account_holder.id)
    for i in range(1, 18):  # 3 minute wait
        logging.info(f"Sleeping for 10 seconds while waiting for callback attempt ({activation.account_holder_id})...")
        sleep(10)
        polaris_db_session.refresh(activation)
        if activation.attempts > 0:
            break
    assert activation.attempts > 0


@then(parsers.parse("the account holder activation is in {status} state"))
def check_enrolment_callback_status(polaris_db_session: "Session", status: str, request_context: dict) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    activation = get_account_holder_activation(polaris_db_session, account_holder.id)
    assert activation.status == status.upper()


def assert_account_holder_activation_status_transition(
    polaris_db_session: "Session",
    activation: AccountHolderActivation,
    *,
    new_status: str,
    # Note: This corresponds to up to 3 minutes wait time.
    # This may need adjusting if the interval of the scheduler is changed or
    # the number of retries is adjusted as the retry backs off.
    wait_times: int = 18,
    wait_duration_secs: int = 10,
) -> AccountHolderActivation:
    for _ in range(wait_times):
        # wait for callback process to handle the callback
        logging.info(f"Sleeping for {wait_duration_secs} seconds...")
        sleep(wait_duration_secs)
        polaris_db_session.refresh(activation)
        if activation.status == new_status:
            break
        else:
            logging.info(
                f"Still waiting for callback status transition to {new_status} "
                f"({activation.account_holder_id} status: {activation.status})"
            )
    assert activation.status == new_status


@then(parsers.parse("the account holder activation completes successfully"))
def check_account_holder_activation_completes_successfully(
    polaris_db_session: "Session", request_context: dict
) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    activation = get_account_holder_activation(polaris_db_session, account_holder.id)
    assert_account_holder_activation_status_transition(polaris_db_session, activation, new_status="SUCCESS")


@then(parsers.parse("the account holder activation is marked as {status} and is not retried"))
def check_account_holder_activation_is_failed(
    polaris_db_session: "Session", status: str, request_context: dict
) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    activation = get_account_holder_activation(polaris_db_session, account_holder.id)
    assert_account_holder_activation_status_transition(polaris_db_session, activation, new_status=status)
    assert activation.next_attempt_time is None


def get_callback_url(
    *,
    status_code: Optional[int] = None,
    num_failures: Optional[int] = None,
    timeout_seconds: Optional[int] = None,
) -> str:
    if status_code is None:
        location = f"/enrol/callback/timeout-{timeout_seconds or 60}"
    elif status_code == 200:
        location = "/enrol/callback/success"
    elif status_code == 500 and num_failures is not None:
        location = f"/enrol/callback/retry-{num_failures}"
    else:
        location = f"/enrol/callback/error-{status_code}"
    return f"{settings.MOCK_SERVICE_BASE_URL}{location}"


def alter_callback_url(
    polaris_db_session: "Session",
    request_context: dict,
    *,
    status_code: Optional[int] = None,
    num_failures: Optional[int] = None,
    timeout_seconds: Optional[int] = None,
) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    activation = get_account_holder_activation(polaris_db_session, account_holder.id)
    activation.callback_url = get_callback_url(
        status_code=status_code, num_failures=num_failures, timeout_seconds=timeout_seconds
    )
    polaris_db_session.add(activation)
    polaris_db_session.commit()


@when(parsers.parse("the callback URL is known to produce an HTTP {status_code:d} response"))
@then(parsers.parse("the callback URL is known to produce an HTTP {status_code:d} response"))
def alter_callback_url_to_produce_xxx_response(
    polaris_db_session: "Session", status_code: int, request_context: dict
) -> None:
    alter_callback_url(polaris_db_session, request_context, status_code=status_code)


@when(parsers.parse("the callback URL is known to produce {num_failures:d} consecutive HTTP 500 error responses"))
def alter_callback_url_to_produce_error(
    polaris_db_session: "Session", num_failures: int, request_context: dict
) -> None:
    alter_callback_url(polaris_db_session, request_context, status_code=500, num_failures=num_failures)


@when(parsers.parse("the callback URL is known to timeout after {timeout_seconds:d} seconds"))
def alter_callback_url_to_produce_timeout(
    polaris_db_session: "Session", timeout_seconds: int, request_context: dict
) -> None:
    alter_callback_url(polaris_db_session, request_context, status_code=None, timeout_seconds=timeout_seconds)


def response_to_json(response: "Response") -> dict:
    try:
        response_json = response.json()
    except JSONDecodeError or Exception:
        raise Exception(f"Empty response and the response Status Code is {str(response.status_code)}")
    return response_json
