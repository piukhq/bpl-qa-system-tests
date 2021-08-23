import json
import logging
import uuid

from typing import TYPE_CHECKING

from deepdiff import DeepDiff
from pytest_bdd import parsers, then, when

from tests.customer_management_api.api_requests.accounts import (
    send_get_accounts,
    send_invalid_get_accounts,
    send_malformed_get_accounts,
)
from tests.customer_management_api.api_requests.base import get_headers
from tests.customer_management_api.response_fixtures.accounts import AccountsResponses
from tests.customer_management_api.response_fixtures.shared import account_holder_details_response_body

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

accounts_responses = AccountsResponses()


@then(parsers.parse("I get a {response_fixture} accounts response body"))
def check_accounts_response(response_fixture: str, request_context: dict, polaris_db_session: "Session") -> None:
    resp = request_context["response"]
    diff = None

    if response_fixture == "success":
        expected_response_body = account_holder_details_response_body(
            polaris_db_session, request_context["account_holder"].id
        )

        diff = DeepDiff(resp.json(), expected_response_body, significant_digits=2)

    else:
        expected_response_body = accounts_responses.get_json(response_fixture)

    logging.info(
        f"POST accounts expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST accounts actual response: {json.dumps(resp.json(), indent=4)}"
    )

    if diff is not None:
        assert not diff
    else:
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
