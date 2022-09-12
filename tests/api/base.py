import json
import logging

from enum import Enum

import settings

from settings import POLARIS_API_AUTH_TOKEN, POLARIS_BASE_URL, VELA_API_AUTH_TOKEN, VELA_BASE_URL


class Endpoints(str, Enum):
    ENROL = "/accounts/enrolment"
    GETBYCREDENTIALS = "/accounts/getbycredentials"
    ACCOUNTS = "/accounts/"
    TRANSACTION = "/transaction"
    STATUSCHANGE = "/campaigns/status_change"

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


def get_polaris_url(retailer_slug: str, endpoint: Endpoints) -> str:
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


def get_callback_url(
    *,
    num_failures: int | None = None,
    status_code: int | None = None,
    timeout_seconds: int | None = 60,
) -> str:
    if status_code is None:
        location = f"/enrol/callback/timeout-{timeout_seconds}"
    elif status_code == 200:
        location = "/enrol/callback/success"
    elif status_code == 500 and num_failures is not None:
        location = f"/enrol/callback/retry-{num_failures}"
    else:
        location = f"/enrol/callback/error-{status_code}"
    return f"{settings.MOCK_SERVICE_BASE_URL}{location}"
