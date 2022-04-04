from typing import TYPE_CHECKING

from tests.api.base import Endpoints, get_vela_headers, get_vela_url
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response


def send_post_campaign_status_change(retailer_slug: str, request_body: dict) -> "Response":
    headers = get_vela_headers()
    url = get_vela_url(retailer_slug, Endpoints.STATUSCHANGE)
    session = retry_session()
    return session.post(url, headers=headers, json=request_body)
