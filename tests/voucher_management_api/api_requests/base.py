import json
import logging

from typing import TYPE_CHECKING

from settings import CARINA_BASE_URL, VOUCHER_MANAGEMENT_API_TOKEN
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response


def get_vm_headers(valid_token: bool = True) -> dict:
    if valid_token:
        token = VOUCHER_MANAGEMENT_API_TOKEN
    else:
        token = "wrong-token"

    return {
        "Accept": "application/json",
        "Authorization": f"Token {token}",
    }


def send_post_vm_request(path: str, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_vm_headers()

    session = retry_session()
    url = f"{CARINA_BASE_URL}{path}"
    logging.info(f"sending POST request to: {url}\n" f"using headers: {json.dumps(headers, indent=4)}")

    resp = session.post(url, headers=headers)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")
    return resp
