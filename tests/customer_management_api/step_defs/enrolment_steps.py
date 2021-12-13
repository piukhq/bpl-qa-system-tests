import json
import logging

from json import JSONDecodeError
from time import sleep
from typing import TYPE_CHECKING, Optional

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from retry_tasks_lib.db.models import RetryTask, TaskTypeKey, TaskTypeKeyValue
from sqlalchemy.future import select

import settings

from db.polaris.models import AccountHolder
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
from tests.customer_management_api.db_actions.retry_tasks import get_latest_callback_task_for_account_holder
from tests.customer_management_api.payloads.enrolment import (
    all_required_and_all_optional_credentials,
    bad_field_validation_request_body,
    malformed_request_body,
    missing_credentials_request_body,
)
from tests.customer_management_api.response_fixtures.enrolment import EnrolResponses
from tests.customer_management_api.step_defs.shared_steps import (
    enrol_account_holder,
    enrol_missing_channel_header,
    enrol_missing_third_party_identifier,
)

if TYPE_CHECKING:
    from requests import Response
    from sqlalchemy.orm import Session


enrol_responses = EnrolResponses()


@given(parse("There is an existing account holder with the same email in the database for {retailer}"))
def post_enrolment_existing_account_holder(retailer: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer
    request_body = all_required_and_all_optional_credentials()
    resp = send_post_enrolment(retailer, request_body)
    assert resp.status_code == 202


# fmt: off
@when(parse("I Enrol a {retailer_slug} account holder passing in all required and all optional fields with a callback URL known to produce an HTTP {status_code:d} response"))  # noqa: E501
# fmt: on
def post_enrolment_with_known_callback_side_effect(retailer_slug: str, status_code: int, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context, callback_url=get_callback_url(status_code=status_code))


# fmt: off
@when(parse("I Enrol a {retailer_slug} account holder passing in all required and all optional fields with a callback URL known to produce {num_failures:d} consecutive HTTP {status_code:d} responses"))  # noqa: E501
# fmt: on
def post_enrolment_with_known_repeated_callback_side_effect(
    retailer_slug: str, num_failures: int, status_code: int, request_context: dict
) -> None:
    enrol_account_holder(
        retailer_slug,
        request_context,
        callback_url=get_callback_url(status_code=status_code, num_failures=num_failures),
    )


# fmt: off
@when(parse("I Enrol a {retailer_slug} account holder passing in all required and all optional fields with a callback URL known to timeout after {timeout_secs:d} seconds"))  # noqa: E501
# fmt: on
def post_enrolment_with_known_callback_timeout(retailer_slug: str, timeout_secs: int, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context, callback_url=get_callback_url(timeout_seconds=timeout_secs))


@when(parse("I Enrol a {retailer_slug} account holder passing in only required fields"))
def post_enrolment_only_required_fields(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context, incl_optional_fields=False)


@when(parse("I Enrol a {retailer_slug} account holder with an malformed request"))
def post_malformed_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = malformed_request_body()
    resp = send_malformed_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@given(parse("I Enrol a {retailer_slug} account holder with an missing fields in request"))
def post_missing_credential_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = missing_credentials_request_body()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response: {resp.json()}, status code: {resp.status_code}")


@given(parse("I Enrol a {retailer_slug} account holder and passing in fields will fail validation request"))
def post_enrolment_with_wrongly_formatted_values(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = bad_field_validation_request_body()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response: {resp.json()}, status code: {resp.status_code}")


@given(parse("I Enrol a {retailer_slug} account holder with an invalid token"))
def post_enrolment_invalid_token(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    resp = send_invalid_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response: {resp.json()}, status code: {resp.status_code}")
    assert resp.status_code == 401


@given(parse("I POST a {retailer_slug} account holder enrol request without a channel HTTP header"))
def post_no_channel_header(retailer_slug: str, request_context: dict) -> None:
    enrol_missing_channel_header(retailer_slug, request_context)


@given(
    parse("I POST a {retailer_slug} account holder enrol request omitting third_party_identifier from the request body")
)
def post_no_third_party_identifier(retailer_slug: str, request_context: dict) -> None:
    enrol_missing_third_party_identifier(retailer_slug, request_context)


@when(parse("I Enrol a {retailer_slug} account holder " "passing in the same email as an existing account holder"))
def post_enrolment_with_previous_request_details(retailer_slug: str, request_context: dict) -> None:
    existing_request_data = json.loads(request_context["response"].request.body)
    existing_email = existing_request_data["credentials"]["email"]

    new_request_body = all_required_and_all_optional_credentials()
    new_request_body["credentials"]["email"] = existing_email

    retailer_slug = request_context["retailer_slug"]
    resp = send_post_enrolment(retailer_slug, new_request_body)
    request_context["response"] = resp


@then("the account holder is activated")
def check_account_holder_activated(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder, "account holder not found from request_context"
    for i in range(1, 18):  # 3 minute wait
        logging.info(
            f"Sleeping for 10 seconds while waiting for account activation (account holder id: {account_holder.id})..."
        )
        sleep(10)
        polaris_db_session.refresh(account_holder)
        if account_holder.status == "ACTIVE":
            break
    assert account_holder.status == "ACTIVE"
    assert account_holder.account_number is not None
    assert len(account_holder.account_holder_campaign_balance_collection) == 1


@then(parse("I get a {response_fixture} enrol response body"))
def check_enrolment_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = enrol_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        f"POST enrol expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST enrol actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body


@then(parse("all fields I sent in the enrol request are saved in the database"))
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


@then(parse("the account holder is not saved in the database"))
def check_account_holder_is_not_saved_in_db(polaris_db_session: "Session", request_context: dict) -> None:
    assert get_account_holder_from_request_data(polaris_db_session, request_context) is None


@then(parse("the account holder is saved in the database"))
def check_account_holder_is_saved_in_db(polaris_db_session: "Session", request_context: dict) -> None:
    assert get_account_holder_from_request_data(polaris_db_session, request_context) is not None


@then(parse("an enrolment callback task is saved in the database"))
def check_account_holder_activation_is_saved_in_db(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    callback_task = get_latest_callback_task_for_account_holder(polaris_db_session, account_holder.id)
    assert callback_task is not None
    assert settings.MOCK_SERVICE_BASE_URL in callback_task.get_params()["callback_url"]
    assert callback_task.get_params()["third_party_identifier"] == "identifier"


@then(parse("the enrolment callback task is tried"))
def check_enrolment_callback_is_tried(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    callback_task = get_latest_callback_task_for_account_holder(polaris_db_session, account_holder.id)
    for i in range(1, 18):  # 3 minute wait
        logging.info(
            f"Sleeping for 10 seconds while waiting for callback attempt "
            f"({callback_task.get_params()['account_holder_uuid']})..."
        )
        sleep(10)
        polaris_db_session.refresh(callback_task)
        if callback_task.attempts > 0:
            break
    assert callback_task.attempts > 0


def assert_task_status_transition(
    polaris_db_session: "Session",
    task: RetryTask,
    *,
    new_status: str,
    # Note: This corresponds to up to 3 minutes wait time.
    # This may need adjusting if the interval of the scheduler is changed or
    # the number of retries is adjusted as the retry backs off.
    wait_times: int = 18,
    wait_duration_secs: int = 10,
) -> RetryTask:
    for _ in range(wait_times):
        # wait for callback process to handle the callback
        logging.info(f"Sleeping for {wait_duration_secs} seconds...")
        sleep(wait_duration_secs)
        polaris_db_session.refresh(task)
        if task.status.name == new_status:
            break
        else:
            logging.info(
                f"Still waiting for {task.task_type.name} task status transition to {new_status} "
                f"(current status: {task.status})"
            )
    assert task.status.name == new_status


@then(parse("the enrolment callback task status is {status}"))
def check_enrolment_callback_status(polaris_db_session: "Session", request_context: dict, status: str) -> None:
    account_holder = get_account_holder_from_request_data(polaris_db_session, request_context)
    assert account_holder is not None
    callback_task = get_latest_callback_task_for_account_holder(polaris_db_session, account_holder.id)
    assert_task_status_transition(polaris_db_session, callback_task, new_status=status.upper())
    request_context["callback_task"] = callback_task


@then(parse("the enrolment callback task is not retried"))
def check_callback_task_next_attempt_time(polaris_db_session: "Session", request_context: dict) -> None:
    assert request_context["callback_task"].next_attempt_time is None


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
    callback_task = get_latest_callback_task_for_account_holder(polaris_db_session, account_holder.id)
    key_val = (
        polaris_db_session.execute(
            select(TaskTypeKeyValue)
            .join(TaskTypeKey)
            .where(
                TaskTypeKeyValue.retry_task_id == callback_task.retry_task_id,
                TaskTypeKey.name == "callback_url",
            )
        )
        .unique()
        .scalar_one()
    )
    key_val.value = get_callback_url(
        status_code=status_code, num_failures=num_failures, timeout_seconds=timeout_seconds
    )
    polaris_db_session.commit()


@when(parse("the callback URL is known to produce an HTTP {status_code:d} response"))
@then(parse("the callback URL is known to produce an HTTP {status_code:d} response"))
def alter_callback_url_to_produce_xxx_response(
    polaris_db_session: "Session", status_code: int, request_context: dict
) -> None:
    alter_callback_url(polaris_db_session, request_context, status_code=status_code)


@when(parse("the callback URL is known to produce {num_failures:d} consecutive HTTP 500 error responses"))
def alter_callback_url_to_produce_error(
    polaris_db_session: "Session", num_failures: int, request_context: dict
) -> None:
    alter_callback_url(polaris_db_session, request_context, status_code=500, num_failures=num_failures)


@when(parse("the callback URL is known to timeout after {timeout_seconds:d} seconds"))
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
