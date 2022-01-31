import uuid

from typing import TYPE_CHECKING, Union

from settings import CARINA_API_AUTH_TOKEN, CARINA_BASE_URL
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response

default_headers = {
    "Authorization": f"Token {CARINA_API_AUTH_TOKEN}",
}


def _send_post_reward_allocation(
    retailer_slug: str, reward_slug: str, request_body: Union[dict, str], headers: dict
) -> "Response":

    return retry_session().post(
        f"{CARINA_BASE_URL}/{retailer_slug}/rewards/{reward_slug}/allocation",
        json=request_body,
        headers=headers,
    )


def send_post_reward_allocation(
    retailer_slug: str, reward_slug: str, request_body: dict, auth: bool = True
) -> "Response":
    headers = default_headers.copy()
    headers["Idempotency-Token"] = str(uuid.uuid4())
    if auth is False:
        headers["Authorization"] = "wrong token"

    return _send_post_reward_allocation(retailer_slug, reward_slug, request_body, headers)


def send_post_malformed_reward_allocation(retailer_slug: str, reward_slug: str, request_body: str) -> "Response":
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Token {CARINA_API_AUTH_TOKEN}",
    }
    return retry_session().post(
        f"{CARINA_BASE_URL}/{retailer_slug}/rewards/{reward_slug}/allocation",
        data=request_body,
        headers=headers,
    )
