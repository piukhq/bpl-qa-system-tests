from typing import TYPE_CHECKING, Union

from settings import VELA_API_AUTH_TOKEN, VELA_BASE_URL
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response

default_headers = {"Authorization": f"Token {VELA_API_AUTH_TOKEN}", "Bpl-User-Channel": "channel"}


def _send_post_campaign_status_change(retailer_slug: str, request_body: Union[dict, str], headers: dict) -> "Response":
    return retry_session().post(
        f"{VELA_BASE_URL}/{retailer_slug}/campaigns/status_change",
        json=request_body,
        headers=headers,
    )


def send_post_campaign_status_change(retailer_slug: str, request_body: dict, auth: bool = True) -> "Response":
    headers = default_headers.copy()
    if auth is False:
        headers["Authorization"] = "wrong token"

    return _send_post_campaign_status_change(retailer_slug, request_body, headers)


def send_post_malformed_campaign_status_change(retailer_slug: str, request_body: str) -> "Response":
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Token {VELA_API_AUTH_TOKEN}",
    }
    return retry_session().post(
        f"{VELA_BASE_URL}/{retailer_slug}/campaigns/status_change",
        data=request_body,
        headers=headers,
    )
