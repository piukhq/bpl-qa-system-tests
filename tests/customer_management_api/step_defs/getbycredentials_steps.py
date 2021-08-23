import json
import logging
from typing import TYPE_CHECKING

from deepdiff import DeepDiff
from pytest_bdd import parsers, then, when

from tests.customer_management_api.api_requests.getbycredentials import (
    send_invalid_post_getbycredentials,
    send_malformed_post_getbycredentials,
    send_post_getbycredentials,
)
from tests.customer_management_api.db_actions.account_holder import get_account_holder
from tests.customer_management_api.db_actions.retailer import get_retailer
from tests.customer_management_api.payloads.getbycredentials import (
    all_required_credentials,
    malformed_request_body,
    missing_credentials_request_body,
    non_existent_user_credentials,
    wrong_validation_request_body,
)
from tests.customer_management_api.response_fixtures.getbycredentials import GetByCredentialsResponses
from tests.customer_management_api.response_fixtures.shared import account_holder_details_response_body

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

getbycredentials_responses = GetByCredentialsResponses


@when(parsers.parse("I post getbycredentials a {retailer_slug} account holder passing in all required credentials"))
def post_getbycredentials(polaris_db_session: "Session", retailer_slug: str, request_context: dict) -> None:
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    retailer = get_retailer(polaris_db_session, retailer_slug)

    if request_context.get("account_holder_exists", True):
        account_holder = get_account_holder(polaris_db_session, email, retailer)
        request_context["account_holder"] = account_holder
        request_body = all_required_credentials(account_holder)
    else:
        request_body = non_existent_user_credentials(email, retailer.account_number_prefix)

    request_context["retailer_slug"] = retailer_slug
    resp = send_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when("I post getbycredentials an invalid-retailer's account holder passing in all required credentials")
def post_getbycredentials_invalid_retailer(request_context: dict) -> None:
    request_body = all_required_credentials()
    request_context["retailer_slug"] = "invalid-retailer"
    resp = send_post_getbycredentials("invalid-retailer", request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when(parsers.parse("I getbycredentials a {retailer_slug} account holder with an malformed request"))
def post_malformed_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = malformed_request_body()
    resp = send_malformed_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when(parsers.parse("I getbycredentials a {retailer_slug} account holder with a missing field in the request"))
def post_missing_field_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = missing_credentials_request_body()
    resp = send_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when(parsers.parse("I getbycredentials a {retailer_slug} account holder passing in fields that will fail validation"))
def post_wrong_validation_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = wrong_validation_request_body()
    resp = send_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@when(parsers.parse("I getbycredentials a {retailer_slug} account holder with an invalid authorisation token"))
def post_invalid_token_request(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_credentials()
    resp = send_invalid_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@then(parsers.parse("I get a {response_fixture} getbycredentials response body"))
def check_getbycredentials_response(response_fixture: str, request_context: dict,
                                    polaris_db_session: "Session") -> None:
    resp = request_context["response"]
    diff = None

    if response_fixture == "success":
        expected_response_body = account_holder_details_response_body(
            polaris_db_session, request_context["account_holder"].id
        )

        diff = DeepDiff(resp.json(), expected_response_body, significant_digits=2)

    else:
        expected_response_body = getbycredentials_responses.get_json(response_fixture)

    logging.info(
        f"POST accounts expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST accounts actual response: {json.dumps(resp.json(), indent=4)}"
    )

    if diff is not None:
        assert not diff
    else:
        assert resp.json() == expected_response_body
