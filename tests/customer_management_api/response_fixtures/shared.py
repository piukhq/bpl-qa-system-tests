from datetime import timezone
from typing import TYPE_CHECKING

from tests.customer_management_api.db_actions.account_holder import get_account_holder_by_id

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def account_holder_details_response_body(polaris_db_session: "Session", account_holder_id: "UUID") -> dict:
    account_holder = get_account_holder_by_id(polaris_db_session, account_holder_id)
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


def account_holder_status_response_body(polaris_db_session: "Session", account_holder_id: "UUID") -> dict:
    account_holder = get_account_holder_by_id(polaris_db_session, account_holder_id)
    return {
        "status": account_holder.status.lower(),
    }
