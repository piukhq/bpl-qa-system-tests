from typing import TYPE_CHECKING

from tests.api.base import Endpoints, get_polaris_headers, get_polaris_url
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response


def send_post_enrolment(retailer_slug: str, request_body: dict, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_polaris_headers()

    url = get_polaris_url(retailer_slug, Endpoints.ENROL)
    session = retry_session()
    return session.post(url, headers=headers, json=request_body)


def send_get_accounts(retailer_slug: str, uuid: str, *, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_polaris_headers()

    url = get_polaris_url(retailer_slug, Endpoints.ACCOUNTS) + uuid
    session = retry_session()
    return session.get(url, headers=headers)


def send_number_of_accounts(num_of_account: str, retailer_slug: str, uuid: str, *, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_polaris_headers()

    url = get_polaris_url(retailer_slug, Endpoints.ACCOUNTS) + uuid + "?tx_qty=" + num_of_account
    session = retry_session()
    return session.get(url, headers=headers)


def send_number_of_accounts_by_post_credential(
    num_of_account: str, retailer_slug: str, request_body: dict, *, headers: dict = None
) -> "Response":
    if headers is None:
        headers = get_polaris_headers()

    url = get_polaris_url(retailer_slug, Endpoints.GETBYCREDENTIALS) + "?tx_qty=" + num_of_account
    session = retry_session()
    return session.post(url, headers=headers, json=request_body)


def send_get_accounts_by_credential(retailer_slug: str, request_body: dict, headers: dict = None) -> "Response":
    if headers is None:
        headers = get_polaris_headers()

    url = get_polaris_url(retailer_slug, Endpoints.GETBYCREDENTIALS)
    session = retry_session()
    return session.post(url, headers=headers, json=request_body)
