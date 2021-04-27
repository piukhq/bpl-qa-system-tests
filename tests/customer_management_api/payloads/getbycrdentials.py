import json
import logging
import random

from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from db.models import AccountHolder


def _get_random_account_number(prefix: str) -> str:
    # nb: valid until we change the max length for account numbers
    return f"{prefix}{str(random.randint(1, (10 ** 10) - 1)).zfill(10)}"


def _get_random_email() -> str:
    return f"pytest{uuid4()}@bink.com"


def all_required_credentials(account_holder: "AccountHolder" = None) -> dict:
    if account_holder:
        payload = {
            "email": account_holder.email,
            "account_number": account_holder.account_number,
        }

    else:
        payload = {
            "email": _get_random_email(),
            "account_number": _get_random_account_number("TEST"),
        }

    logging.info("`Request body for POST getbycredentials " + json.dumps(payload, indent=4))
    return payload


def non_existent_user_credentials(email: str, prefix: str) -> dict:
    payload = {
        "email": email,
        "account_number": _get_random_account_number(prefix),
    }
    logging.info("`Request body for POST getbycredentials " + json.dumps(payload, indent=4))
    return payload


def malformed_request_body() -> str:
    return "malformed request"


def missing_credentials_request_body() -> dict:
    payload = {
        "email": _get_random_email(),
        # missing account_number
    }

    logging.info("`Request body for missing credentials  " + json.dumps(payload, indent=4))
    return payload


def wrong_validation_request_body() -> dict:
    payload = {
        "email": "not a valid email",
        "date_of_birth": "01/12/1990",
        "phone": 999,
        "account_number": _get_random_account_number("TEST"),
    }
    logging.info("`Request body for missing validation " + json.dumps(payload, indent=4))
    return payload
