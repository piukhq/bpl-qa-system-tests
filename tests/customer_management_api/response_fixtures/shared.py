from datetime import timezone
from typing import TYPE_CHECKING

from tests.customer_management_api.db_actions.account_holder import get_account_holder_by_id

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def account_holder_details_response_body(db_session: "Session", account_holder_id: "UUID") -> dict:
    account_holder = get_account_holder_by_id(db_session, account_holder_id)
    created_date_timestamp = int(account_holder.created_at.replace(tzinfo=timezone.utc).timestamp())
    account_holder_balances = [balance for balance in account_holder.current_balances.values()]
    for balance in account_holder_balances:
        balance["value"] = balance["value"] / 100

    return {
        "UUID": str(account_holder.id),
        "email": account_holder.email,
        "created_date": created_date_timestamp,
        "status": account_holder.status.lower(),
        "account_number": account_holder.account_number,
        "current_balances": account_holder_balances,
        "transaction_history": [],
        "vouchers": [],
    }


INVALID_RETAILER = {
    "display_message": "Requested retailer is invalid.",
    "error": "INVALID_RETAILER",
}

INVALID_TOKEN = {
    "display_message": "Supplied token is invalid.",
    "error": "INVALID_TOKEN",
}

MALFORMED_REQUEST = {
    "display_message": "Malformed request.",
    "error": "MALFORMED_REQUEST",
}

NO_ACCOUNT_FOUND = {
    "display_message": "Account not found for provided credentials.",
    "error": "NO_ACCOUNT_FOUND",
}

CREDENTIALS_VALIDATION_FAILED = [
    {
        "display_message": "Submitted credentials did not pass validation.",
        "error": "VALIDATION_FAILED",
        "fields": ["email"],
    }
]

THIRD_PARTY_IDENTIFIER_VALIDATION_FAILED = [
    {
        "display_message": "Missing credentials from request.",
        "error": "MISSING_FIELDS",
        "fields": ["third_party_identifier"],
    }
]
ENROL_VALIDATION_FAILED = [
    {
        "display_message": "Submitted credentials did not pass validation.",
        "error": "VALIDATION_FAILED",
        "fields": ["email", "date_of_birth", "phone", "address_line2", "city"],
    }
]

MISSING_CHANNEL_HEADER = {
    "display_message": "Missing header",
    "error": "MISSING_HTTP_HEADER",
    "fields": [
        "bpl-user-channel",
    ],
}
