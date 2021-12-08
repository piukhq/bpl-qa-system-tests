import json
import logging
import uuid

from typing import TYPE_CHECKING

from deepdiff import DeepDiff
from pytest_bdd import then, when
from pytest_bdd.parsers import parse

from tests.customer_management_api.api_requests.accounts import (
    send_get_accounts_status,
    send_invalid_get_accounts_status,
)
from tests.customer_management_api.db_actions.account_holder import get_active_account_holder
from tests.customer_management_api.db_actions.retailer import get_retailer
from tests.customer_management_api.response_fixtures.accounts_status import AccountsStatusResponses
from tests.customer_management_api.response_fixtures.shared import account_holder_status_response_body

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

accounts_status_responses = AccountsStatusResponses()


@when(parse("I send a get /accounts request for a {retailer_slug} account holder status by UUID"))
def get_account_status(polaris_db_session: "Session", request_context: dict, retailer_slug: str) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    retailer = get_retailer(polaris_db_session, retailer_slug)

    if request_context.get("account_holder_exists", True):
        account_holder = get_active_account_holder(polaris_db_session, email, retailer)
        assert account_holder is not None
        request_context["account_holder"] = account_holder
        account_holder_id = str(account_holder.id)
    else:
        account_holder_id = str(uuid.uuid4())

    resp = send_get_accounts_status(retailer_slug, account_holder_id)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@then(parse("I get a {response_fixture} accounts status response body"))
def check_accounts_status_response(response_fixture: str, request_context: dict, polaris_db_session: "Session") -> None:
    resp = request_context["response"]
    diff = None

    if response_fixture == "success":
        expected_response_body = account_holder_status_response_body(
            polaris_db_session, request_context["account_holder"].id
        )

        diff = DeepDiff(resp.json(), expected_response_body, significant_digits=2)

    else:
        expected_response_body = accounts_status_responses.get_json(response_fixture)

    logging.info(
        f"POST accounts expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST accounts actual response: {json.dumps(resp.json(), indent=4)}"
    )

    if diff is not None:
        assert not diff
    else:
        assert resp.json() == expected_response_body


# fmt: off
@when(parse("I send a get /accounts request for a {retailer_slug} account holder status by UUID with an invalid authorisation token"))  # noqa: E501
# fmt: on
def get_accounts_status_invalid_token_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    resp = send_invalid_get_accounts_status(retailer_slug, str(uuid.uuid4()))
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")
