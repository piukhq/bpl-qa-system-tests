import time

from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, RetryTaskStatuses, TaskType, TaskTypeKey, TaskTypeKeyValue
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_latest_callback_task_for_account_holder(cosmos_db_session: "Session") -> RetryTask:
    task_name = "enrolment-callback"
    task_type = get_task_type_from_task_name(cosmos_db_session, task_name)
    for i in (1, 3, 5, 10):
        time.sleep(i)
        callback_task = (
            cosmos_db_session.execute(
                select(RetryTask)
                .where(RetryTask.task_type_id == task_type.task_type_id)
                .order_by(RetryTask.created_at.desc())
            )
            .scalars()
            .first()
        )
        if callback_task:
            break

    return callback_task


def get_task_type_from_task_name(db_session: "Session", task_name: str) -> TaskType:
    task_type = (
        db_session.execute(
            select(TaskType).filter(
                TaskType.name == task_name,
            )
        )
        .scalars()
        .first()
    )
    return task_type


def get_latest_task(
    db_session: "Session",
    task_name: str,
) -> RetryTask:
    return (
        db_session.execute(
            select(RetryTask).join(TaskType).where(TaskType.name == task_name).order_by(RetryTask.created_at.desc())
        )
        .scalars()
        .first()
    )


def get_retry_task_audit_data(
    db_session: "Session",
    task_name: str,
) -> RetryTaskStatuses:
    audit_data = db_session.execute(
        select(RetryTask.audit_data).where(RetryTask.task_type_id == TaskType.task_type_id, TaskType.name == task_name)
    ).first()
    return audit_data


def get_tasks_by_type_and_key_value(
    db_session: "Session", task_type_name: str, task_type_key_name: str, task_type_key_value_value: str
) -> list[RetryTask]:
    tasks = (
        db_session.execute(
            select(RetryTask)
            .join(TaskType)
            .join(TaskTypeKey)
            .join(
                TaskTypeKeyValue,
                (TaskTypeKeyValue.task_type_key_id == TaskTypeKey.task_type_key_id)
                & (TaskTypeKeyValue.retry_task_id == RetryTask.retry_task_id),
            )
            .where(
                TaskType.name == task_type_name,
                TaskTypeKey.name == task_type_key_name,
                TaskTypeKeyValue.value == task_type_key_value_value,
            )
        )
        .unique()
        .scalars()
        .all()
    )
    db_session.rollback()  # this is quite important :D
    return tasks
