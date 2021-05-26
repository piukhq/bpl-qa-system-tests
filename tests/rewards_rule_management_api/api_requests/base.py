import json
import logging
from typing import TYPE_CHECKING

from settings import REWARDS_RULE_MANAGEMENT_API_TOKEN, VELA_BASE_URL
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response


def get_rrm_headers(valid_token: bool = True) -> dict:
    if valid_token:
        token = REWARDS_RULE_MANAGEMENT_API_TOKEN
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
