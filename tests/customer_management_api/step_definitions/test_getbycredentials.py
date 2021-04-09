import json
import logging

from pytest_bdd import then, parsers, scenarios, when, given

from tests.customer_management_api.db.account_holder import get_account_holder
from tests.customer_management_api.payloads.enrolment import all_required_and_all_optional_credentials
from tests.customer_management_api.payloads.getbycrdentials import all_required_credentials
from tests.customer_management_api.requests.enrolment import send_post_enrolment
from tests.customer_management_api.requests.getbycredentials import send_post_getbycredentials
from tests.customer_management_api.response_fixtures.getbycredentials import GetByCredentialsResponses

scenarios("customer_management_api/getbycredentials/")

getbycredentials_responses = GetByCredentialsResponses()


@then(parsers.parse("I get a {response_fixture} enrol response body"))
def check_enrolment_response(response_fixture: str, request_context: dict):
    expected_response_body = getbycredentials_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        "POST enrol expected response: {} \n actual response: {}".format(
            json.dumps(expected_response_body), resp.json()
        )
    )
    assert resp.json() == expected_response_body


@then(parsers.parse("I get a success getbycredentials response body"))
def check_enrolment_response(request_context: dict):
    expected_response_body = {
        "UUID": str(request_context["account_holder"].id),
        "email": request_context["account_holder"].email,
        "created_at": request_context["account_holder"].created_at.isoformat(),
        "status": "active",
        "account_number": request_context["account_holder"].account_number
    }
    resp = request_context["response"]
    logging.info(
        "POST getbycredentials expected response: {} \n actual response: {}".format(
            json.dumps(expected_response_body), resp.json()
        )
    )
    assert resp.json() == expected_response_body


@when(parsers.parse("I post getbycredentials a {retailer_slug} account holder passing in all required credentials"))
def post_getbycredentials(retailer_slug: str, request_context: dict):
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    account_holder = get_account_holder(email, retailer_slug)
    request_context["account_holder"] = account_holder

    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_credentials(account_holder)
    resp = send_post_getbycredentials(retailer_slug, request_body)
    request_context["response"] = resp


@given(parsers.parse("I previously enrolled a {retailer_slug} account holder "
                     "passing in all required and all optional fields"))
@when(parsers.parse("I Enrol a {retailer_slug} account holder passing in all required and all optional fields"))
def post_enrolment(retailer_slug: str, request_context: dict):
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp


@given(parsers.parse("the previous response returned a HTTP {status_code:d} status code"))
@then(parsers.parse("I receive a HTTP {status_code:d} status code in the response"))
def check_enrolment_status_code(status_code: int, request_context: dict) -> None:
    resp = request_context["response"]
    logging.info(f"POST Enrol response HTTP status code: {resp.status_code}")
    assert resp.status_code == status_code
