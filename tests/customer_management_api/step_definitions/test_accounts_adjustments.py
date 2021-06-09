import uuid

from random import randint
from typing import TYPE_CHECKING, Tuple

from pytest_bdd import given, parsers, scenarios, then, when

from tests.customer_management_api.api_requests.accounts_adjustments import send_post_accounts_adjustments
from tests.customer_management_api.response_fixtures.adjustments import AdjustmentsResponses
from tests.customer_management_api.step_definitions.shared import (
    check_account_holder_is_active,
    check_response_status_code,
    enrol_account_holder,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from db.polaris.models import AccountHolder

scenarios("customer_management_api/accounts_adjustments/")


def _get_adjustment_account_holder_and_payload(request_context: dict) -> Tuple["AccountHolder", dict]:
    account_holder = request_context["account_holder"]
    campaign_slug, balance = next(iter(account_holder.current_balances.items()))
    balance_change = randint(5, 5000)
    payload = {
        "balance_change": balance_change,
        "campaign_slug": campaign_slug,
    }
    request_context["request_details"] = payload
    request_context["request_details"]["old_balance"] = balance["value"]

    return account_holder, payload


@given(parsers.parse("I previously successfully enrolled a {retailer_slug} account holder"))
def setup_account_holder(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context)


@given(parsers.parse("I received a HTTP {status_code:d} status code response"))
def setup_check_enrolment_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "Enrol")


@given(parsers.parse("the enrolled account holder has been activated and i know its current balances"))
def check_adjustments_account_holder_is_active(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = check_account_holder_is_active(polaris_db_session, request_context)
    request_context["account_holder"] = account_holder


@when(
    parsers.parse(
        "I post the balance adjustment for a {retailer_slug} account holder passing in all required credentials"
    )
)
def send_adjustment_request(retailer_slug: str, request_context: dict) -> None:
    account_holder, payload = _get_adjustment_account_holder_and_payload(request_context)
    resp = send_post_accounts_adjustments(retailer_slug, account_holder.id, payload)

    request_context["response"] = resp


@then(parsers.parse("I receive a HTTP {status_code:d} status code in the adjustments response"))
def check_adjustments_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "adjustments")


@then(parsers.parse("The account holder's balance {action} updated in the database"))
@then(parsers.parse("The account holder's balance {action} updated in the database only once"))
def check_updated_balance(action: str, request_context: dict, polaris_db_session: "Session") -> None:
    account_holder = request_context["account_holder"]
    polaris_db_session.refresh(account_holder)
    campaign_slug = request_context["request_details"]["campaign_slug"]
    old_balance = request_context["request_details"]["old_balance"]
    balance_change = request_context["request_details"]["balance_change"]

    if action == "is":
        assert account_holder.current_balances[campaign_slug]["value"] == old_balance + balance_change
    elif action == "is not":
        assert account_holder.current_balances[campaign_slug]["value"] == old_balance
    else:
        raise ValueError(f"{action} is an invalid value for action")


@when(
    parsers.parse(
        "I post the balance adjustment for a {retailer_slug} account holder passing in all required credentials twice"
    )
)
def send_adjustment_request_twice(retailer_slug: str, request_context: dict) -> None:
    account_holder, payload = _get_adjustment_account_holder_and_payload(request_context)
    idempotency_token = str(uuid.uuid4())
    resp_1 = send_post_accounts_adjustments(retailer_slug, account_holder.id, payload, idempotency_token)
    resp_2 = send_post_accounts_adjustments(retailer_slug, account_holder.id, payload, idempotency_token)

    request_context["response"] = resp_1
    request_context["response_2"] = resp_2


@when(
    parsers.parse(
        "I post the balance adjustment for a {retailer_slug} account holder passing in an invalid idempotency token"
    )
)
def send_adjustment_request_wrong_token(retailer_slug: str, request_context: dict) -> None:
    account_holder, payload = _get_adjustment_account_holder_and_payload(request_context)
    idempotency_token = "not a uuid"
    resp = send_post_accounts_adjustments(retailer_slug, account_holder.id, payload, idempotency_token)

    request_context["response"] = resp


@then(parsers.parse("I receive a HTTP {status_code:d} status code in the adjustments response for both"))
def check_adjustments_response_status_code_twice(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "adjustments")
    resp_2 = request_context["response_2"]
    assert resp_2.status_code == status_code


@then(parsers.parse("I get a {response_fixture} adjustments response body"))
def check_adjustments_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = AdjustmentsResponses.get_json(response_fixture)
    resp = request_context["response"]

    assert resp.json() == expected_response_body
