import time

from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, RetryTaskStatuses, TaskType
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_latest_callback_task_for_account_holder(polaris_db_session: "Session") -> RetryTask:
    task_name = "enrolment-callback"
    task_type = get_task_type_from_task_name(polaris_db_session, task_name)
    for i in (1, 3, 5, 10):
        time.sleep(i)
        callback_task = (
            polaris_db_session.execute(
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


def get_task_status(
    db_session: "Session",
    task_name: str,
) -> RetryTaskStatuses:
    task_type_id = db_session.execute(select(TaskType.task_type_id).where(TaskType.name == task_name)).scalar_one()
    return db_session.execute(select(RetryTask.status).where(RetryTask.task_type_id == task_type_id)).first()


def get_retry_task_audit_data(
    db_session: "Session",
    task_name: str,
) -> RetryTaskStatuses:
    task_type_id = db_session.execute(select(TaskType.task_type_id).where(TaskType.name == task_name)).scalar_one()
    return db_session.execute(select(RetryTask.audit_data).where(RetryTask.task_type_id == task_type_id)).first()


def get_task_attempts(db_session: "Session", task_name: str) -> RetryTask:
    task_type_id = db_session.execute(select(TaskType.task_type_id).where(TaskType.name == task_name)).scalar_one()
    return db_session.execute(select(RetryTask.attempts).where(RetryTask.task_type_id == task_type_id)).first()
