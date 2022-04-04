from typing import TYPE_CHECKING

from sqlalchemy.future import select

from db.vela.models import Campaign, RetryTask, RewardRule, TaskType, TaskTypeKey, TaskTypeKeyValue

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_reward_adjustment_task_status(
    vela_db_session: "Session",
    campaign_slug: str,
) -> str:
    return (
        vela_db_session.execute(
            select(RetryTask.status)
            .where(
                TaskType.name == "reward-adjustment",
                TaskTypeKey.task_type_id == TaskType.task_type_id,
                TaskTypeKey.name == "campaign_slug",
                TaskTypeKeyValue.task_type_key_id == TaskTypeKey.task_type_key_id,
                TaskTypeKeyValue.value == campaign_slug,
                RetryTask.retry_task_id == TaskTypeKeyValue.retry_task_id,
            )
            .order_by(RetryTask.created_at.desc())
        )
        .scalars()
        .first()
    )


def get_campaign_by_slug(
    vela_db_session: "Session",
    campaign_slug: str,
) -> Campaign:
    return vela_db_session.execute(select(Campaign).where(Campaign.slug == campaign_slug)).scalar_one()


def get_reward_goal_by_campaign_id(
    vela_db_session: "Session",
    campaign_id: int,
) -> int:
    return vela_db_session.execute(
        select(RewardRule.reward_goal).where(RewardRule.campaign_id == campaign_id)
    ).scalar_one()
