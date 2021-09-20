from typing import TYPE_CHECKING

from tests.customer_management_api.db_actions.account_holder import get_account_holder_by_id

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def account_holder_details_response_body(polaris_db_session: "Session", account_holder_id: "UUID") -> dict:
    account_holder = get_account_holder_by_id(polaris_db_session, account_holder_id)
    return {
        "UUID": str(account_holder.id),
        "email": account_holder.email,
        "status": account_holder.status.lower(),
        "account_number": account_holder.account_number,
        "current_balances": [
            {"value": balance.balance / 100, "campaign_slug": balance.campaign_slug}
            for balance in account_holder.account_holder_campaign_balance_collection
        ],
        "transaction_history": [],
        "vouchers": [],
    }


def account_holder_status_response_body(polaris_db_session: "Session", account_holder_id: "UUID") -> dict:
    account_holder = get_account_holder_by_id(polaris_db_session, account_holder_id)
    return {
        "status": account_holder.status.lower(),
    }
