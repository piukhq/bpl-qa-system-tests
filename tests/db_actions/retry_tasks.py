import time

from typing import TYPE_CHECKING, Union
from uuid import UUID

from retry_tasks_lib.db.models import RetryTask, RetryTaskStatuses, TaskType, TaskTypeKey, TaskTypeKeyValue
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_latest_callback_task_for_account_holder(
    polaris_db_session: "Session", account_holder_uuid: Union[str, UUID]
) -> RetryTask:
    for i in (1, 3, 5, 10):
        time.sleep(i)
        callback_task = (
            polaris_db_session.execute(
                select(RetryTask)
                .where(
                    RetryTask.task_type_id == TaskType.task_type_id,
                    TaskType.name == "enrolment-callback",
                    TaskTypeKeyValue.task_type_key_id == TaskTypeKey.task_type_key_id,
                    TaskTypeKeyValue.value == str(account_holder_uuid),
                    RetryTask.retry_task_id == TaskTypeKeyValue.retry_task_id,
                )
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
