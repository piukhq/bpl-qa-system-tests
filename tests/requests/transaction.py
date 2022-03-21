import json
import logging
from typing import TYPE_CHECKING

from tests.api.base import Endpoints, get_vela_headers, get_vela_url, get_polaris_headers, get_polaris_url
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response



def post_transaction_request(request_body: dict, retailer_slug: str, request_context: dict) -> None:

    headers = get_vela_headers()
    url = get_vela_url(retailer_slug, Endpoints.TRANSACTION)
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


def post_adjustments_request(request_body: dict, retailer_slug: str, account_holder_uuid: str, request_context: dict, auth: bool, idempotency_token: str = None) -> "Response":

    headers = get_polaris_headers()
    url = get_polaris_url(retailer_slug, Endpoints.ADJUSTMENTS, account_holder_uuid=account_holder_uuid)
    session = retry_session()
    resp = session.post(url, headers=headers, json=request_body)

    logging.info(
        f"POST adjustments headers: {headers}\n"
        f"POST adjustments URL:{url}\n"
        f"POST adjustments request body: {json.dumps(request_body, indent=4)}\n"
        f"POST adjustments response: {json.dumps(resp.json(), indent=4)}"
    )
    request_context["resp"] = resp
    request_context["request_payload"] = request_body
