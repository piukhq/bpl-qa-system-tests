import json
import logging

from enum import Enum
from typing import Any

from settings import POLARIS_API_AUTH_TOKEN, POLARIS_BASE_URL, VELA_API_AUTH_TOKEN, VELA_BASE_URL


class Endpoints(str, Enum):
    ENROL = "/accounts/enrolment"
    GETBYCREDENTIALS = "/accounts/getbycredentials"
    ACCOUNTS = "/accounts/"
    TRANSACTION = "/transaction"
    ADJUSTMENTS = "/accounts/{account_holder_uuid}/adjustments"

    @property
    def endpoint(self) -> str:
        return self.split("/")[-1]


def get_polaris_headers(channel_header: bool = True, valid_token: bool = True) -> dict:
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


def get_polaris_url(retailer_slug: str, endpoint: Endpoints, **kwargs: Any) -> str:
    if kwargs:
        endpoint = endpoint.format(**kwargs)
    return f"{POLARIS_BASE_URL}/{retailer_slug}" + endpoint


def get_vela_headers(channel_header: bool = True, valid_token: bool = True) -> dict:
    if valid_token:
        auth_token = VELA_API_AUTH_TOKEN
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


def get_vela_url(retailer_slug: str, endpoint: Endpoints) -> str:
    return f"{VELA_BASE_URL}/{retailer_slug}" + endpoint
