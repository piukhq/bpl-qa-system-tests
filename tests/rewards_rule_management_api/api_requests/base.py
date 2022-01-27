import json
import logging

from typing import TYPE_CHECKING

import requests

from settings import VELA_API_AUTH_TOKEN, VELA_BASE_URL
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response


def get_rrm_headers(valid_token: bool = True) -> dict:
    if valid_token:
        token = VELA_API_AUTH_TOKEN
    else:
        token = "wrong-token"

    return {
        "Accept": "application/json",
        "Authorization": f"Token {token}",
    }


def send_get_rrm_request(path: str, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_rrm_headers()

    session = retry_session()
    url = f"{VELA_BASE_URL}{path}"
    logging.info(f"sending GET request to: {url}\n" f"using headers: {json.dumps(headers, indent=4)}")

    resp = session.get(url, headers=headers)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")
    return resp


def post_transaction_request(payload: dict, retailer_slug: str, token: str, request_context: dict) -> None:
    if token != "correct":
        headers = get_rrm_headers(valid_token=False)
    else:
        headers = get_rrm_headers()

    resp = requests.post(
        f"{VELA_BASE_URL}/{retailer_slug}/transaction",
        json=payload,
        headers=headers,
    )
    logging.info(
        f"Post transaction headers: {headers}\n"
        f"Post transaction URL:{VELA_BASE_URL}/{retailer_slug}/transaction\n"
        f"Post transaction request body: {json.dumps(payload, indent=4)}\n"
        f"POST Transactions response: {json.dumps(resp.json(), indent=4)}"
    )
    request_context["resp"] = resp
    request_context["request_payload"] = payload
