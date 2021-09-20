import logging
import uuid

from random import randint
from typing import TYPE_CHECKING, Tuple

from pytest_bdd import parsers, then, when

from tests.customer_management_api.api_requests.accounts_adjustments import send_post_accounts_adjustments
from tests.customer_management_api.response_fixtures.adjustments import AdjustmentsResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _get_adjustment_account_holder_and_payload(request_context: dict) -> Tuple[str, dict]:
    balance = request_context["balance"]
    balance_change = randint(5, 5000)
    payload = {
        "balance_change": balance_change,
        "campaign_slug": balance.campaign_slug,
    }
    request_context["request_details"] = payload
    request_context["request_details"]["old_balance"] = balance.balance

    return balance.account_holder_id, payload


@when(parsers.parse("I post the balance adjustment for a {retailer_slug} account holder with a {token} auth token"))
def send_adjustment_request(retailer_slug: str, token: str, request_context: dict) -> None:
    if "balance" in request_context:
        account_holder_id, payload = _get_adjustment_account_holder_and_payload(request_context)
    else:
        account_holder_id = str(uuid.uuid4())
        payload = {
            "balance_change": 100,
            "campaign_slug": "campaign-slug",
        }

    if token == "valid":
        auth = True
    elif token == "invalid":
        auth = False
    else:
        raise ValueError(f"{token} is an invalid value for token")

    resp = send_post_accounts_adjustments(retailer_slug, account_holder_id, payload, auth=auth)

    request_context["response"] = resp


@then(parsers.parse("The account holder's balance {action} updated in the database"))
@then(parsers.parse("The account holder's balance {action} updated in the database only once"))
def check_updated_balance(action: str, request_context: dict, polaris_db_session: "Session") -> None:
    balance = request_context["balance"]
    polaris_db_session.refresh(balance)
    old_balance = request_context["request_details"]["old_balance"]
    balance_change = request_context["request_details"]["balance_change"]

    if action == "is":
        assert balance.balance == old_balance + balance_change
    elif action == "is not":
        assert balance.balance == old_balance
    else:
        raise ValueError(f"{action} is an invalid value for action")


@when(
    parsers.parse(
        "I post the balance adjustment for a {retailer_slug} account holder passing in all required credentials twice"
    )
)
def send_adjustment_request_twice(retailer_slug: str, request_context: dict) -> None:
    account_holder_id, payload = _get_adjustment_account_holder_and_payload(request_context)
    idempotency_token = str(uuid.uuid4())
    resp_1 = send_post_accounts_adjustments(retailer_slug, account_holder_id, payload, idempotency_token)
    resp_2 = send_post_accounts_adjustments(retailer_slug, account_holder_id, payload, idempotency_token)

    request_context["response"] = resp_1
    request_context["response_2"] = resp_2


@when(
    parsers.parse(
        "I post the balance adjustment for a {retailer_slug} account holder passing in an invalid idempotency token"
    )
)
def send_adjustment_request_wrong_token(retailer_slug: str, request_context: dict) -> None:
    account_holder_id, payload = _get_adjustment_account_holder_and_payload(request_context)
    idempotency_token = "not a uuid"
    resp = send_post_accounts_adjustments(retailer_slug, account_holder_id, payload, idempotency_token)

    request_context["response"] = resp


@then(parsers.parse("I receive a HTTP {status_code:d} status code in the adjustments response for both"))
def check_adjustments_response_status_code_twice(status_code: int, request_context: dict) -> None:
    resp = request_context["response"]
    assert resp.status_code == status_code
    logging.info(f"First response HTTP status code: {resp.status_code}")
    resp_2 = request_context["response_2"]
    assert resp_2.status_code == status_code
    logging.info(f"Second response HTTP status code: {resp_2.status_code}")


@then(parsers.parse("I get a {response_fixture} adjustments response body"))
def check_adjustments_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = AdjustmentsResponses.get_json(response_fixture)
    resp = request_context["response"]

    assert resp.json() == expected_response_body
