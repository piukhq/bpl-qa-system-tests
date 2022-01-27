import time

from typing import TYPE_CHECKING

from retry_tasks_lib.db.models import RetryTask, TaskTypeKey, TaskTypeKeyValue
from sqlalchemy.future import select
from sqlalchemy.sql.functions import count

from db.carina.models import Rewards, RewardConfig
from db.polaris.models import AccountHolderReward

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_count_unallocated_rewards_by_reward_config(carina_db_session: "Session", reward_configs_ids: list[int]) -> int:
    return carina_db_session.scalar(
        select(count(Rewards.id)).where(Rewards.reward_config_id.in_(reward_configs_ids), Rewards.allocated.is_(False))
    )


def get_reward_configs_ids_by_retailer(carina_db_session: "Session", retailer_slug: str) -> list[int]:
    return (
        carina_db_session.execute(select(RewardConfig.id).where(RewardConfig.retailer_slug == retailer_slug))
        .scalars()
        .all()
    )


def get_reward_config(carina_db_session: "Session", retailer_slug: str) -> RewardConfig:
    return (
        carina_db_session.execute(select(RewardConfig).where(RewardConfig.retailer_slug == retailer_slug))
        .scalars()
        .first()
    )


def get_reward_config_with_available_rewards(carina_db_session: "Session", retailer_slug: str) -> RewardConfig:
    return (
        carina_db_session.execute(
            select(RewardConfig).where(
                RewardConfig.retailer_slug == retailer_slug,
                Rewards.reward_config_id == RewardConfig.id,
                Rewards.allocated.is_(False),
            )
        )
        .scalars()
        .first()
    )


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


def get_allocated_reward(polaris_db_session: "Session", reward_uuid: int) -> AccountHolderReward:
    for i in (1, 3, 5, 10):
        time.sleep(i)
        reward = polaris_db_session.execute(
            select(AccountHolderReward).where(AccountHolderReward.reward_uuid == reward_uuid)
        ).scalar_one()
        if reward:
            break

    return reward
