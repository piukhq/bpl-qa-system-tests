from typing import TYPE_CHECKING

from tests.api.base import Endpoints, send_post_request

if TYPE_CHECKING:
    from requests import Response


def send_post_enrolment(retailer_slug: str, request_body: dict, headers: dict = None) -> "Response":
    return send_post_request(retailer_slug, request_body, Endpoints.ENROL, headers=headers)
