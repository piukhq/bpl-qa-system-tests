import time
from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskTypeKey, TaskTypeKeyValue
from sqlalchemy.future import select

from db.carina.models import Voucher, VoucherConfig
from db.polaris.models import AccountHolderVoucher

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_count_unallocated_vouchers(carina_db_session: "Session") -> int:
    return carina_db_session.query(Voucher).filter_by(allocated=False).count()


def get_count_voucher_configs(carina_db_session: "Session", retailer_slug: str) -> int:
    return carina_db_session.query(VoucherConfig).filter_by(retailer_slug=retailer_slug).count()


def get_voucher_config(carina_db_session: "Session", retailer_slug: str) -> VoucherConfig:
    return carina_db_session.query(VoucherConfig).filter_by(retailer_slug=retailer_slug).first()


def get_last_created_voucher_allocation(carina_db_session: "Session", voucher_config_id: int) -> RetryTask:
    for i in (1, 3, 5, 10):
        time.sleep(i)
        allocation_task = (
            carina_db_session.execute(
                select(RetryTask)
                .where(
                    TaskTypeKey.name == "voucher_allocation",
                    TaskTypeKeyValue.task_type_key_id == TaskTypeKey.task_type_key_id,
                    TaskTypeKeyValue.value == voucher_config_id,
                    RetryTask.retry_task_id == TaskTypeKeyValue.retry_task_id,
                )
                .order_by(RetryTask.created_at.desc())
            )
            .scalars()
            .first()
        )
        if allocation_task:
            break

    return allocation_task


def get_allocated_voucher(polaris_db_session: "Session", voucher_id: int) -> AccountHolderVoucher:
    for i in (1, 3, 5, 10):
        time.sleep(i)
        voucher = polaris_db_session.query(AccountHolderVoucher).filter_by(voucher_id=voucher_id).one()
        if voucher:
            break

    return voucher
