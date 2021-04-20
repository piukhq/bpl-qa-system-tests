import logging

from tests.customer_management_api.api_requests.enrolment import send_post_enrolment
from tests.customer_management_api.payloads.enrolment import all_required_and_all_optional_credentials


def check_response_status_code(status_code: int, request_context: dict, endpoint: str) -> None:
    resp = request_context["response"]
    logging.info(f"POST {endpoint} response HTTP status code: {resp.status_code}")
    assert resp.status_code == status_code


def enrol_account_holder(retailer_slug: str, request_context: dict) -> None:
    request_context["retailer_slug"] = retailer_slug
    request_body = all_required_and_all_optional_credentials()
    resp = send_post_enrolment(retailer_slug, request_body)
    request_context["response"] = resp
