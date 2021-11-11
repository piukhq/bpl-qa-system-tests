import logging
import uuid

from typing import TYPE_CHECKING, Literal, Optional, Union

from settings import CUSTOMER_MANAGEMENT_API_TOKEN, POLARIS_BASE_URL
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response

default_headers = {
    "Authorization": f"Token {CUSTOMER_MANAGEMENT_API_TOKEN}",
}


def send_post_accounts_voucher(
    retailer_slug: str,
    account_holder_id: str,
    request_body: Union[dict, str],
    token_validity: Literal["valid", "invalid"],
    headers: Optional[dict] = None,
) -> "Response":
    headers = headers or default_headers.copy()
    headers["Idempotency-Token"] = str(uuid.uuid4())
    logging.info(f"Headers for POST Vouchers API : {headers}")
    if token_validity == "invalid":
        headers = headers | {"Authorization": "WRONG TOKEN"}
    return retry_session().post(
        f"{POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_id}/vouchers", json=request_body, headers=headers
    )
