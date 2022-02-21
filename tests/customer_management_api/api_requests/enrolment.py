from typing import TYPE_CHECKING

from tests.customer_management_api.api_requests.base import send_post_request, Endpoints

if TYPE_CHECKING:
    from requests import Response


def send_post_enrolment(retailer_slug: str, request_body: dict, headers: dict = None) -> "Response":
    return send_post_request(retailer_slug, request_body, Endpoints.ENROL, headers=headers)