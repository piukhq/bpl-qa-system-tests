import json

import pytest
from pytest_bdd import parsers, when, then, scenarios, given

from tests.customer_management_api.db.account_holder import get_account_holder, get_account_holder_profile, \
    assert_enrol_request_body_with_account_holder_table, assert_enrol_request_body_with_account_holder_profile_table
from tests.customer_management_api.db.retailer import get_retailer
from tests.customer_management_api.payloads.enrolment import all_required_and_all_optional_credentials
from tests.customer_management_api.requests.enrolment import send_post_enrolment
from tests.customer_management_api.response_fixtures.enrolment import EnrolResponses

scenarios("customer_management_api/enrolment/")

enrol_responses = EnrolResponses()


@pytest.fixture(scope='function')
def request_context():
    return {}


@given(parsers.parse("There is an existing user with the same email in the database for {retailer}"))
def post_enrolment_existing_account_holder(retailer):
    request_context["retailer_slug"] = retailer
    request_body = all_required_and_all_optional_credentials()
    resp = send_post_enrolment(retailer, request_body)
    assert resp.status_code == 202


@given(parsers.parse("I previously enrolled a {retailer_slug} account holder "
                     "passing in all required and all optional fields"))
@when(parsers.parse("I Enrol a {retailer_slug} User account passing in all required and all optional fields"))
def post_enrolment(retailer_slug: str, request_context: dict):
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp


@when(parsers.parse("I Enrol a {retailer_slug} account holder "
                    "passing in the same email as an existing account holder"))
def post_enrolment_with_previous_request_details(retailer_slug: str, request_context: dict):
    existing_request_data = json.loads(request_context["response"].request.body)
    existing_email = existing_request_data["credentials"]["email"]

    new_request_body = all_required_and_all_optional_credentials()
    new_request_body["credentials"]["email"] = existing_email

    retailer_slug = request_context["retailer_slug"]
    resp = send_post_enrolment(retailer_slug, new_request_body)
    request_context["response"] = resp


@given(parsers.parse("the previous response returned a HTTP {status_code:d} status code"))
@then(parsers.parse("I receive a HTTP {status_code:d} status code in the response"))
def check_enrolment_status_code(status_code: int, request_context: dict):
    resp = request_context["response"]
    assert resp.status_code == status_code


@then(parsers.parse("I get a {response_fixture} response body"))
def check_enrolment_response(response_fixture: str, request_context: dict):
    expected_response_body = enrol_responses.get_json(response_fixture)
    resp = request_context["response"]
    assert resp.json() == expected_response_body


@then(parsers.parse("all fields I sent in the enrol request are saved in the database"))
def check_all_fields_saved_in_db(request_context: dict):
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    retailer = get_retailer(retailer_slug)

    account_holder = get_account_holder(email, retailer_slug)
    account_holder_id = account_holder.id
    account_holder_profile = get_account_holder_profile(account_holder_id)

    assert_enrol_request_body_with_account_holder_table(account_holder, request_body, retailer.id)
    assert_enrol_request_body_with_account_holder_profile_table(account_holder_profile, request_body)


@then(parsers.parse("the account holder is not saved in the database"))
def check_user_is_not_saved_in_db(request_context: dict):
    request_body = json.loads(request_context["response"].request.body)
    email = request_body["credentials"]["email"]
    retailer_slug = request_context["retailer_slug"]
    user = get_account_holder(email, retailer_slug)
    assert user is None
