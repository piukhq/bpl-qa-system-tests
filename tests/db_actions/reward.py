# @pytest.fixture(scope="function")
# def get_reward_config(carina_db_session: "Session") -> Callable:
#     def func(retailer_id: int, reward_slug: str | None = None) -> RewardConfig:
#         query = select(RewardConfig).where(RewardConfig.retailer_id == retailer_id)
#         if reward_slug is not None:
#             query = query.where(RewardConfig.reward_slug == reward_slug)
#         return carina_db_session.execute(query).scalars().first()
#
#     return func
import time

from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from retry_tasks_lib.db.models import RetryTask, TaskType, TaskTypeKey, TaskTypeKeyValue
from sqlalchemy.future import select

from db.cosmos.models import AccountHolder, Campaign, Retailer, Reward
from tests.db_actions.cosmos import get_reward_config_id

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_last_created_reward_issuance_task(carina_db_session: "Session", reward_config_id: int) -> RetryTask:
    for i in (1, 3, 5, 10):
        time.sleep(i)
        allocation_task = (
            carina_db_session.execute(
                select(RetryTask)
                .where(
                    TaskType.task_type_id == RetryTask.task_type_id,
                    TaskType.name == "reward-issuance",
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


def assign_rewards(
    cosmos_db_session: "Session",
    reward_slug: str,
    retailer_config: Retailer,
    standard_campaign: Campaign,
    rewards_n: int,
    deleted_status: str,
    account_holder: Optional[AccountHolder],
) -> list[Reward]:
    account_holder = None if account_holder == "None" else account_holder
    deleted_status_bool = deleted_status == "true"
    reward_config_id = get_reward_config_id(cosmos_db_session=cosmos_db_session, reward_slug=reward_slug)
    rewards: list[Reward] = []

    if rewards_n > 0:
        for i in range(rewards_n):
            reward = Reward(
                reward_uuid=str(uuid4()),
                reward_config_id=reward_config_id,
                account_holder_id=account_holder,
                code=f"{reward_slug}/{i}",
                deleted=deleted_status_bool,
                issued_date=None,
                expiry_date=None,
                redeemed_date=None,
                cancelled_date=None,
                associated_url="abc@bink.com",
                retailer_id=retailer_config.id,
                campaign_id=standard_campaign.id,
            )
            cosmos_db_session.add(reward)
            cosmos_db_session.commit()
            rewards.append(reward)

    return rewards
