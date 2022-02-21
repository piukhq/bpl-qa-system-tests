from typing import TYPE_CHECKING, Optional

from db.polaris.models import AccountHolder

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

def get_account_holder(polaris_db_session: "Session", email: str) -> Optional[AccountHolder]:
    return polaris_db_session.query(AccountHolder).filter_by(email=email).first()