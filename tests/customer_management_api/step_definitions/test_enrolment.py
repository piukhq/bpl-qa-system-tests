import json

import pytest
from pytest_bdd import parsers, when, then, scenarios

from tests.customer_management_api.db.account_holder import get_account_holder, get_user_profile
from tests.customer_management_api.payloads.enrolment import all_required_and_all_optional_credentials
from tests.customer_management_api.requests.enrolment import send_post_enrolment
from tests.customer_management_api.response_fixtures.enrolment import EnrolResponses

scenarios("customer_management_api/enrolment/")

enrol_responses = EnrolResponses()


@pytest.fixture(scope='function')
def request_context():
    return {}


@when(parsers.parse("I Enrol a {retailer} User account passing in all required and all optional fields"))
def post_enrolment(retailer: str, request_context: dict):
    request_context["retailer_slug"] = retailer
    request_body = all_required_and_all_optional_credentials()
    resp = send_post_enrolment(retailer, request_body)
    request_context["response"] = resp


@then(parsers.parse("I receive a HTTP {status_code:d} status code in the response"))
def check_enrolment_status_code(status_code: int, request_context: dict):
    resp = request_context["response"]
    assert resp.status_code == status_code


@then(parsers.parse("I get a {response_fixture} response body"))
def check_enrolment_response(response_fixture: str, request_context: dict):
    expected_response_body = enrol_responses.get_json(response_fixture)
    resp = request_context["response"]
    assert resp.json() == expected_response_body


# split me into two parts?
@then(parsers.parse("all fields I sent in the enrol request are saved in the database"))
def check_all_fields_saved_in_db(request_context: dict):
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    user = get_account_holder(email, retailer_slug)
    uuid = user.id
    user_profile = get_user_profile(uuid)


@then(parsers.parse("the account holder is not saved in the database"))
def check_user_is_not_saved_in_db(request_context: dict):
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    user = get_account_holder(email, retailer_slug)
    assert user is None
