from enum import Enum
import logging
import json
from settings import ENV_BASE_URL, CUSTOMER_MANAGEMENT_API_TOKEN


class Endpoints(str, Enum):
    ENROL = "/accounts/enrolment"
    GETBYCREDENTIALS = "/accounts/getbycredentials"


def get_headers() -> dict:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        'Authorization': f"Token {CUSTOMER_MANAGEMENT_API_TOKEN}"
    }
    logging.info(f"Header is : {json.dumps(headers, indent=4)}")
    return headers


def get_invalid_headers() -> dict:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Token token"
    }
    return headers


def get_url(retailer_slug: str, endpoint: Endpoints) -> str:
    return ENV_BASE_URL + f"/bpl/loyalty/{retailer_slug}" + endpoint
