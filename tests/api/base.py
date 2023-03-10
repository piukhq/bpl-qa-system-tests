import json
import logging

from enum import Enum

import settings

from settings import (
    ACCOUNTS_API_BASE_URL,
    CAMPAINGS_API_BASE_URL,
    PUBLIC_API_BASE_URL,
    ACCOUNT_API_AUTH_TOKEN,
    TRANSACTIONS_API_BASE_URL,
    TX_API_AUTH_TOKEN,
    CAMPAIGN_API_AUTH_TOKEN,
)


class Endpoints(str, Enum):
    ENROL = "/accounts/enrolment"
    GETBYCREDENTIALS = "/accounts/getbycredentials"
    ACCOUNTS = "/accounts/"
    STATUSCHANGE = "/status-change"
    MARKETING_UNSUBSCRIBE = "/marketing/unsubscribe?u="

    @property
    def endpoint(self) -> str:
        return self.split("/")[-1]


def get_accounts_headers(channel_header: bool = True, valid_token: bool = True) -> dict:
    if valid_token:
        auth_token = ACCOUNT_API_AUTH_TOKEN
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


def get_transaction_headers(channel_header: bool = True, valid_token: bool = True) -> dict:
    if valid_token:
        auth_token = TX_API_AUTH_TOKEN
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


def get_campaign_headers(channel_header: bool = True, valid_token: bool = True) -> dict:
    if valid_token:
        auth_token = CAMPAIGN_API_AUTH_TOKEN
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


def get_accounts_url(retailer_slug: str, endpoint: Endpoints) -> str:
    return f"{ACCOUNTS_API_BASE_URL}/{retailer_slug}" + endpoint


def get_transaction_api(retailer_slug: str) -> str:
    return f"{TRANSACTIONS_API_BASE_URL}/" + retailer_slug


def get_campaign_mngt(retailer_slug: str, endpoint: Endpoints) -> str:
    return f"{CAMPAINGS_API_BASE_URL}/" + retailer_slug + endpoint


def get_public_api(retailer_slug: str, endpoint: Endpoints) -> str:
    return f"{PUBLIC_API_BASE_URL}/" + retailer_slug + endpoint


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
