import uuid
from typing import TYPE_CHECKING, Union

from settings import CARINA_BASE_URL, VOUCHER_MANAGEMENT_API_TOKEN
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response

default_headers = {
    "Authorization": f"Token {VOUCHER_MANAGEMENT_API_TOKEN}",
}


def _send_post_voucher_allocation(
    retailer_slug: str, voucher_type_slug: str, request_body: Union[dict, str], headers: dict
) -> "Response":

    return retry_session().post(
        f"{CARINA_BASE_URL}/{retailer_slug}/vouchers/{voucher_type_slug}/allocation",
        json=request_body,
        headers=headers,
    )


def send_post_voucher_allocation(
    retailer_slug: str, voucher_type_slug: str, request_body: dict, auth: bool = True
) -> "Response":
    headers = default_headers.copy()
    headers["Idempotency-Token"] = str(uuid.uuid4())
    if auth is False:
        headers["Authorization"] = "wrong token"

    return _send_post_voucher_allocation(retailer_slug, voucher_type_slug, request_body, headers)


def send_post_malformed_voucher_allocation(retailer_slug: str, voucher_type_slug: str, request_body: str) -> "Response":
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Token {VOUCHER_MANAGEMENT_API_TOKEN}",
    }
    return retry_session().post(
        f"{CARINA_BASE_URL}/{retailer_slug}/vouchers/{voucher_type_slug}/allocation",
        data=request_body,
        headers=headers,
    )
