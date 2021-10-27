import time

from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskTypeKey, TaskTypeKeyValue
from sqlalchemy.future import select
from sqlalchemy.sql.functions import count

from db.carina.models import Voucher, VoucherConfig
from db.polaris.models import AccountHolderVoucher

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_count_unallocated_vouchers_by_voucher_config(
    carina_db_session: "Session", voucher_configs_ids: list[int]
) -> int:
    return carina_db_session.scalar(
        select(count(Voucher.id)).where(
            Voucher.voucher_config_id.in_(voucher_configs_ids), Voucher.allocated.is_(False)
        )
    )


def get_voucher_configs_ids_by_retailer(carina_db_session: "Session", retailer_slug: str) -> list[int]:
    return (
        carina_db_session.execute(select(VoucherConfig.id).where(VoucherConfig.retailer_slug == retailer_slug))
        .scalars()
        .all()
    )


def get_voucher_config(carina_db_session: "Session", retailer_slug: str) -> VoucherConfig:
    return (
        carina_db_session.execute(select(VoucherConfig).where(VoucherConfig.retailer_slug == retailer_slug))
        .scalars()
        .first()
    )


def get_voucher_config_with_available_vouchers(carina_db_session: "Session", retailer_slug: str) -> VoucherConfig:
    return (
        carina_db_session.execute(
            select(VoucherConfig).where(
                VoucherConfig.retailer_slug == retailer_slug,
                Voucher.voucher_config_id == VoucherConfig.id,
                Voucher.allocated.is_(False),
            )
        )
        .scalars()
        .first()
    )


def get_last_created_voucher_allocation(carina_db_session: "Session", voucher_config_id: int) -> RetryTask:
    for i in (1, 3, 5, 10):
        time.sleep(i)
        allocation_task = (
            carina_db_session.execute(
                select(RetryTask)
                .where(
                    TaskTypeKey.name == "voucher_config_id",
                    TaskTypeKeyValue.task_type_key_id == TaskTypeKey.task_type_key_id,
                    TaskTypeKeyValue.value == str(voucher_config_id),
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
