from typing import TYPE_CHECKING, Optional

from db.carina.models import VoucherAllocation

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_voucher_allocation(carina_db_session: "Session", retailer_slug: str) -> Optional[VoucherAllocation]:
    return carina_db_session.query(VoucherAllocation).filter_by(slug=retailer_slug).first()
