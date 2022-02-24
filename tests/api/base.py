import json
import logging
from enum import Enum
from typing import TYPE_CHECKING

from settings import POLARIS_API_AUTH_TOKEN, POLARIS_BASE_URL
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response


class Endpoints(str, Enum):
    ENROL = "/accounts/enrolment"
    GETBYCREDENTIALS = "/accounts/getbycredentials"
    ACCOUNTS = "/accounts/"

    @property
    def endpoint(self) -> str:
        return self.split("/")[-1]


def get_headers(channel_header: bool = True, valid_token: bool = True) -> dict:
    if valid_token:
        auth_token = POLARIS_API_AUTH_TOKEN
    else:
        auth_token = "incorrect-token"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Token {auth_token}",
    }
    if channel_header:
        headers["bpl-user-channel"] = "user-channel"

    logging.info(f"Headers: {json.dumps(headers, indent=4)}")
    return headers


def get_url(retailer_slug: str, endpoint: Endpoints) -> str:
    return f"{POLARIS_BASE_URL}/{retailer_slug}" + endpoint


def send_post_request(retailer_slug: str, request_body: dict, endpoint: Endpoints, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_headers()

    url = get_url(retailer_slug, endpoint)
    session = retry_session()
    return session.post(url, headers=headers, json=request_body)
