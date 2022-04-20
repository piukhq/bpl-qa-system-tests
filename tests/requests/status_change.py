import json
import logging

from typing import TYPE_CHECKING

from tests.api.base import Endpoints, get_vela_headers, get_vela_url
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response


def send_post_campaign_status_change(request_context: dict, retailer_slug: str, request_body: dict) -> "Response":
    headers = get_vela_headers()
    url = get_vela_url(retailer_slug, Endpoints.STATUSCHANGE)
    session = retry_session()
    resp = session.post(url, headers=headers, json=request_body)
    logging.info(
        f"POST campaign status change headers: {headers}\n"
        f"POST campaign status change URL:{url}\n"
        f"POST campaign status change request body: {json.dumps(request_body, indent=4)}\n"
        f"POST campaign status change response: {json.dumps(resp.json(), indent=4)}"
    )
    request_context["resp"] = resp
    request_context["request_payload"] = request_body

    return resp
