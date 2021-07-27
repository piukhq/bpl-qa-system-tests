from typing import TYPE_CHECKING

from db.carina.models import Voucher, VoucherAllocation, VoucherConfig

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_count_unallocated_vouchers(carina_db_session: "Session") -> int:
    count_unallocated_vouchers = carina_db_session.query(Voucher).filter_by(allocated=False).count()

    return count_unallocated_vouchers


def get_count_voucher_configs(carina_db_session: "Session", retailer_slug: str) -> int:
    return carina_db_session.query(VoucherConfig).filter_by(retailer_slug=retailer_slug).count()


def get_voucher_config(carina_db_session: "Session", retailer_slug: str) -> int:
    return carina_db_session.query(VoucherConfig).filter_by(retailer_slug=retailer_slug).first()


def get_last_created_voucher_allocation(carina_db_session: "Session", voucher_config_id: int) -> VoucherAllocation:
    return (
        carina_db_session.query(VoucherAllocation)
        .filter_by(voucher_config_id=voucher_config_id)
        .order_by(VoucherAllocation.created_at.desc())
        .first()
    )
