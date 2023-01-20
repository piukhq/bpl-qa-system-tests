import time

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import update
from sqlalchemy.future import select

from db.cosmos.models import (
    AccountHolder,
    Campaign,
    CampaignBalance,
    FetchType,
    PendingReward,
    Retailer,
    Reward,
    RewardConfig,
    RewardRule,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_reward_config_id(
    cosmos_db_session: "Session",
    reward_slug: str,
) -> int:
    return cosmos_db_session.execute(
        select(RewardConfig.id).where(
            RewardConfig.reward_slug == reward_slug,
        )
    ).scalar_one()


def get_fetch_type_id(
    cosmos_db_session: "Session",
    fetch_type_name: str,
) -> int:
    return cosmos_db_session.execute(select(FetchType.id).where(FetchType.name == fetch_type_name)).scalar_one()


def get_retailer_id(
    cosmos_db_session: "Session",
    retailer_slug: str,
) -> int:
    return cosmos_db_session.execute(select(Retailer.id).where(Retailer.slug == retailer_slug)).scalar_one()


def get_rewards(cosmos_db_session: "Session", reward_ids: list[str], allocated: bool) -> list[Reward]:
    rewards = (
        cosmos_db_session.execute(select(Reward).where(Reward.id.in_(reward_ids), Reward.allocated.is_(allocated)))
        .scalars()
        .all()
    )
    return rewards


def get_rewards_by_reward_config(cosmos_db_session: "Session", reward_config_id: int, allocated: bool) -> list[Reward]:
    rewards = (
        cosmos_db_session.execute(
            select(Reward).where(Reward.reward_config_id == reward_config_id, Reward.allocated.is_(allocated))
        )
        .scalars()
        .all()
    )
    return rewards


def get_account_holder_for_retailer(polaris_db_session: "Session", retailer_id: int) -> AccountHolder:
    return polaris_db_session.execute(select(AccountHolder).where(retailer_id == retailer_id)).scalar_one()


def get_account_holder_with_email(polaris_db_session: "Session", email: str, retailer_id: int) -> AccountHolder:
    return polaris_db_session.execute(
        select(AccountHolder).where(email == email, retailer_id == retailer_id)
    ).scalar_one()


def get_account_holder_reward(cosmos_db_session: "Session", reward_slug: str, retailer_slug: str) -> list[Reward]:
    return (
        cosmos_db_session.execute(select(Reward).where(reward_slug == reward_slug, retailer_slug == retailer_slug))
        .scalars()
        .all()
    )


def get_pending_rewards(
    polaris_db_session: "Session",
    account_holder: AccountHolder,
    campaign_slug: str,
) -> list[PendingReward]:
    return (
        polaris_db_session.execute(
            select(PendingReward).where(
                campaign_slug == campaign_slug, PendingReward.account_holder_id == account_holder.id
            )
        )
        .scalars()
        .all()
    )


def get_ordered_pending_rewards(
    polaris_db_session: "Session", account_holder: AccountHolder, campaign_slug: str
) -> list[PendingReward]:
    pending_rewards = get_pending_rewards(polaris_db_session, account_holder, campaign_slug)
    return sorted(
        pending_rewards,
        key=lambda x: x.created_at,
    )


def create_rewards_for_existing_account_holder(
    polaris_db_session: "Session",
    *,
    retailer_slug: str,
    reward_count: int,
    account_holder_id: int,
    campaign_slug: str,
    reward_slug: str | None = "reward-test-slug",
    status: str = "ISSUED",
    expiry_date: datetime | None = None,
) -> None:
    rewards = []
    for _ in range(1, int(reward_count) + 1):
        reward = Reward(
            reward_uuid=str(uuid4()),
            code=str(uuid4()),
            issued_date=datetime.now() - timedelta(days=1),
            expiry_date=expiry_date if expiry_date else datetime.now() + timedelta(days=1),
            status=status,
            campaign_slug=campaign_slug,
            reward_slug=reward_slug,
            retailer_slug=retailer_slug,
            idempotency_token=str(uuid4()),
            account_holder_id=account_holder_id,
        )
        rewards.append(reward)

    polaris_db_session.add_all(rewards)
    polaris_db_session.commit()


def create_pending_rewards_for_existing_account_holder(
    cosmos_db_session: "Session",
    retailer_slug: str,
    num_rewards: int,
    account_holder_id: int,
    campaign_slug: str,
    reward_slug: str | None,
    reward_goal: int,
) -> None:
    count = 1
    for _ in range(int(num_rewards)):
        pending_reward = PendingReward(
            created_date=datetime.now() - timedelta(days=1),
            conversion_date=datetime.now() + timedelta(days=1),
            value=reward_goal,
            campaign_slug=campaign_slug,
            reward_slug=reward_slug,
            retailer_slug=retailer_slug,
            account_holder_id=account_holder_id,
            idempotency_token=str(uuid4()),
            count=count,
            total_cost_to_user=reward_goal,
            pending_reward_uuid=str(uuid4()),
        )
        cosmos_db_session.add(pending_reward)

    cosmos_db_session.commit()


def create_pending_rewards_with_all_value_for_existing_account_holder(
    cosmos_db_session: "Session",
    retailer_slug: str,
    conversion_date: date,
    prr_count: int,
    value: int,
    total_cost_to_user: int,
    account_holder_id: int,
    campaign_slug: str,
    reward_slug: str | None,
) -> PendingReward:

    pending_reward = PendingReward(
        created_date=datetime.now() - timedelta(days=1),
        conversion_date=conversion_date,
        value=value,
        campaign_slug=campaign_slug,
        reward_slug=reward_slug,
        retailer_slug=retailer_slug,
        account_holder_id=account_holder_id,
        idempotency_token=str(uuid4()),
        count=prr_count,
        total_cost_to_user=total_cost_to_user,
        pending_reward_uuid=str(uuid4()),
    )
    cosmos_db_session.add(pending_reward)

    cosmos_db_session.commit()
    return pending_reward


def create_balance_for_account_holder(
    cosmos_db_session: "Session", account_holder: AccountHolder, campaign: Campaign, balance: int = 0
) -> None:
    balance = CampaignBalance(account_holder_id=account_holder.id, campaign_slug=campaign.slug, balance=0)
    cosmos_db_session.add(balance)
    cosmos_db_session.commit()


def get_account_holder_balances_for_campaign(
    cosmos_db_session: "Session", account_holders: list[AccountHolder], campaign_slug: str
) -> list[CampaignBalance]:
    return (
        cosmos_db_session.execute(
            select(CampaignBalance).where(
                CampaignBalance.account_holder_id.in_([ah.id for ah in account_holders]),
                CampaignBalance.campaign_slug == campaign_slug,
            )
        )
        .scalars()
        .all()
    )


def update_account_holder_pending_rewards_conversion_date(
    cosmos_db_session: "Session", account_holder: AccountHolder, campaign_slug: str, conversion_date: date
) -> PendingReward:
    pending_reward = cosmos_db_session.execute(
        update(PendingReward)
        .values(conversion_date=conversion_date)
        .where(
            PendingReward.account_holder_id == account_holder.id,
            PendingReward.campaign_slug == campaign_slug,
        )
    )
    cosmos_db_session.commit()
    time.sleep(3)
    return pending_reward


#
# def get_reward_adjustment_task_status(
#     cosmos_db_session: "Session",
#     campaign_slug: str,
# ) -> str:
#     return (
#         cosmos_db_session.execute(
#             select(RetryTask.status)
#             .where(
#                 TaskType.name == "reward-adjustment",
#                 TaskTypeKey.task_type_id == TaskType.task_type_id,
#                 TaskTypeKey.name == "campaign_slug",
#                 TaskTypeKeyValue.task_type_key_id == TaskTypeKey.task_type_key_id,
#                 TaskTypeKeyValue.value == campaign_slug,
#                 RetryTask.retry_task_id == TaskTypeKeyValue.retry_task_id,
#             )
#             .order_by(RetryTask.created_at.desc())
#         )
#         .scalars()
#         .first()
#     )


def get_campaign_by_slug(
    cosmos_db_session: "Session",
    campaign_slug: str,
) -> Campaign:
    return cosmos_db_session.execute(select(Campaign).where(Campaign.slug == campaign_slug)).scalar_one()


def get_reward_goal_by_campaign_id(
    cosmos_db_session: "Session",
    campaign_id: int,
) -> int:
    return cosmos_db_session.execute(
        select(RewardRule.reward_goal).where(RewardRule.campaign_id == campaign_id)
    ).scalar_one()


def get_campaign_status(
    cosmos_db_session: "Session",
    campaign_slug: str,
) -> int:
    return cosmos_db_session.execute(select(Campaign.status).where(Campaign.slug == campaign_slug)).scalar_one()
