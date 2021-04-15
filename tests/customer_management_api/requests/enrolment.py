from typing import TYPE_CHECKING

from .base import send_post_request, send_invalid_post_request, send_malformed_post_request, Endpoints

if TYPE_CHECKING:
    from requests import Response


def send_post_enrolment(retailer_slug: str, request_body: dict) -> "Response":
    return send_post_request(retailer_slug, request_body, Endpoints.ENROL)


def send_malformed_post_enrolment(retailer_slug: str, request_body: str) -> "Response":
    return send_malformed_post_request(retailer_slug, request_body, Endpoints.ENROL)


def send_invalid_post_enrolment(retailer_slug: str, request_body: dict) -> "Response":
    return send_invalid_post_request(retailer_slug, request_body, Endpoints.ENROL)
