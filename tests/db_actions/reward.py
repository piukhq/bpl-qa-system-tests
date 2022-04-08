# @pytest.fixture(scope="function")
# def get_reward_config(carina_db_session: "Session") -> Callable:
#     def func(retailer_id: int, reward_slug: Optional[str] = None) -> RewardConfig:
#         query = select(RewardConfig).where(RewardConfig.retailer_id == retailer_id)
#         if reward_slug is not None:
#             query = query.where(RewardConfig.reward_slug == reward_slug)
#         return carina_db_session.execute(query).scalars().first()
#
#     return func
import time

from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskTypeKey, TaskTypeKeyValue
from sqlalchemy.future import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_last_created_reward_allocation(carina_db_session: "Session", reward_config_id: int) -> RetryTask:
    for i in (1, 3, 5, 10):
        time.sleep(i)
        allocation_task = (
            carina_db_session.execute(
                select(RetryTask)
                .where(
                    TaskTypeKey.name == "reward_config_id",
                    TaskTypeKeyValue.task_type_key_id == TaskTypeKey.task_type_key_id,
                    TaskTypeKeyValue.value == str(reward_config_id),
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
