import json
import logging

from tests.api.base import get_transaction_api, get_vela_headers
from tests.retry_requests import retry_session


def post_transaction_request(request_body: dict, retailer_slug: str, request_context: dict) -> None:

    headers = get_vela_headers()
    url = get_transaction_api(retailer_slug)
    session = retry_session()
    resp = session.post(url, headers=headers, json=request_body)

    logging.info(
        f"Post transaction headers: {headers}\n"
        f"Post transaction URL:{url}\n"
        f"Post transaction request body: {json.dumps(request_body, indent=4)}\n"
        f"POST Transactions response: {json.dumps(resp.json(), indent=4)}"
    )
    request_context["resp"] = resp
    request_context["request_payload"] = request_body
