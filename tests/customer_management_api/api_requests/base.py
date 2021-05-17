import json
import logging

from enum import Enum
from typing import TYPE_CHECKING

from settings import CUSTOMER_MANAGEMENT_API_TOKEN, ENV_BASE_URL
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


def get_headers() -> dict:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Token {CUSTOMER_MANAGEMENT_API_TOKEN}",
        "bpl-user-channel": "user-channel",
    }
    logging.info(f"Headers: {json.dumps(headers, indent=4)}")
    return headers


def get_invalid_headers() -> dict:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Token token",
        "Bpl-User-Channel": "user-channel",
    }
    return headers


def get_url(retailer_slug: str, endpoint: Endpoints) -> str:
    return ENV_BASE_URL + f"/bpl/loyalty/{retailer_slug}" + endpoint


def _send_post_request(retailer_slug: str, endpoint: Endpoints, headers: dict, request_body: str) -> "Response":
    url = get_url(retailer_slug, endpoint)
    session = retry_session()
    logging.info(f"POST {endpoint.endpoint} URL is: {url}")
    return session.post(url, headers=headers, data=request_body)


def send_post_request(retailer_slug: str, request_body: dict, endpoint: Endpoints, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_headers()

    return _send_post_request(retailer_slug, endpoint, headers, json.dumps(request_body))


def send_malformed_post_request(retailer_slug: str, request_body: str, endpoint: Endpoints) -> "Response":
    headers = get_headers()
    return _send_post_request(retailer_slug, endpoint, headers, request_body)


def send_invalid_post_request(retailer_slug: str, request_body: dict, endpoint: Endpoints) -> "Response":
    headers = get_invalid_headers()
    return _send_post_request(retailer_slug, endpoint, headers, json.dumps(request_body))


def _send_get_request(retailer_slug: str, endpoint: Endpoints, param: str, headers: dict) -> "Response":
    url = get_url(retailer_slug, endpoint) + param
    session = retry_session()
    logging.info(f"GET {endpoint.endpoint} URL is: {url}")
    return session.get(url, headers=headers)


def send_get_request(retailer_slug: str, endpoint: Endpoints, param: str, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_headers()

    return _send_get_request(retailer_slug, endpoint, param, headers)


def send_malformed_get_request(retailer_slug: str, endpoint: Endpoints, param: str) -> "Response":
    headers = get_headers()
    return _send_get_request(retailer_slug, endpoint, param, headers)


def send_invalid_get_request(retailer_slug: str, endpoint: Endpoints, param: str) -> "Response":
    headers = get_invalid_headers()
    return _send_get_request(retailer_slug, endpoint, param, headers)
