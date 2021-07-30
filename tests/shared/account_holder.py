from typing import Tuple

from sqlalchemy.orm import Session

from db.polaris.models import AccountHolder, RetailerConfig


def shared_setup_account_holder(
    email: str, status: str, retailer_slug: str, polaris_db_session: Session
) -> Tuple[RetailerConfig, AccountHolder]:
    retailer = polaris_db_session.query(RetailerConfig).filter_by(slug=retailer_slug).first()
    if retailer is None:
        raise ValueError(f"a retailer with slug '{retailer_slug}' was not found in the db.")

    account_status = {"active": "ACTIVE"}.get(status, "PENDING")

    account_holder = polaris_db_session.query(AccountHolder).filter_by(email=email, retailer_id=retailer.id).first()
    if account_holder is None:

        account_holder = AccountHolder(
            email=email,
            retailer_id=retailer.id,
            status=account_status,
            current_balances={},
        )
        polaris_db_session.add(account_holder)
    else:
        account_holder.status = account_status

    polaris_db_session.commit()

    return retailer, account_holder
