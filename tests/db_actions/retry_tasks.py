import time
from typing import TYPE_CHECKING, Union
from uuid import UUID

from retry_tasks_lib.db.models import RetryTask, TaskType, TaskTypeKey, TaskTypeKeyValue
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
