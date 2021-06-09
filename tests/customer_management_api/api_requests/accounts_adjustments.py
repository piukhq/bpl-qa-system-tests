from typing import TYPE_CHECKING, Union
from uuid import uuid4

from settings import CUSTOMER_MANAGEMENT_API_TOKEN, POLARIS_BASE_URL
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response

default_headers = {
    "Authorization": f"Token {CUSTOMER_MANAGEMENT_API_TOKEN}",
    "idempotency-token": str(uuid4()),
}


def _send_post_accounts_adjustments(
    retailer_slug: str, account_holder_id: str, request_body: Union[dict, str], headers: dict
) -> "Response":
    return retry_session().post(
        f"{POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_id}/adjustments",
        json=request_body,
        headers=headers,
    )


def send_post_accounts_adjustments(
    retailer_slug: str, account_holder_id: str, request_body: dict, idempotency_token: str = None
) -> "Response":
    headers = default_headers.copy()
    if idempotency_token:
        headers["idempotency-token"] = idempotency_token

    return _send_post_accounts_adjustments(retailer_slug, account_holder_id, request_body, headers)
