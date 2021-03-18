import pytest
from pytest_bdd import parsers, when, then, scenarios

from tests.customer_management_api.payloads.enrolment import all_required_and_all_optional_credentials
from tests.customer_management_api.requests.enrolment import send_post_enrolment

scenarios("enrolment/")


@pytest.fixture(scope='function')
def request_context():
    return {}


@when(parsers.parse("I Enrol a {retailer} User account passing in all required and all optional fields"))
def post_enrolment(retailer, request_context):
    request_body = all_required_and_all_optional_credentials()
    resp = send_post_enrolment(retailer, request_body)
    request_context["response"] = resp


@then(parsers.parse("I receive a {status_code:d} HTTP status code back with an empty response body"))
def check_enrolment_response(status_code, request_context):
    resp = request_context["response"]
    assert resp.status_code == status_code
    assert "id" in resp.json()


@then(parsers.parse("All fields I sent in the enrol request are saved in the database"))
def check_enrolment_response(request_context):
    request_body = request_context["response"].request
    print(request_body)
