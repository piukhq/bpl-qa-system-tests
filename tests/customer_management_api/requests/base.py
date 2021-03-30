from enum import Enum

from settings import ENV_BASE_URL, CUSTOMER_MANAGEMENT_API_TOKEN


class Endpoints(str, Enum):
    ENROL = "/accounts/enrolment"


def get_headers() -> dict:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization': f"Token {CUSTOMER_MANAGEMENT_API_TOKEN}"
    }
    return headers


def get_url(retailer_slug: str, endpoint: Endpoints) -> str:
    return ENV_BASE_URL + f"/bpl/loyalty/{retailer_slug}" + endpoint
