from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy.future import select

from db.polaris.models import AccountHolder, AccountHolderPendingReward, AccountHolderReward

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_account_holder_for_retailer(polaris_db_session: "Session", retailer_id: int) -> AccountHolder:
    account_holder = polaris_db_session.execute(select(AccountHolder).where(retailer_id == retailer_id)).scalar_one()
    return account_holder


def get_account_holder_with_email(polaris_db_session: "Session", email: str, retailer_id: int) -> AccountHolder:
    account_holder = polaris_db_session.execute(
        select(AccountHolder).where(email == email, retailer_id == retailer_id)
    ).scalar_one()
    return account_holder


def get_account_holder_reward(
    polaris_db_session: "Session", reward_slug: str, retailer_slug: str
) -> list[AccountHolderReward]:
    return (
        polaris_db_session.execute(
            select(AccountHolderReward).where(reward_slug == reward_slug, retailer_slug == retailer_slug)
        )
        .scalars()
        .all()
    )


def get_pending_rewards(
    polaris_db_session: "Session",
    campaign_slug: str,
) -> list[AccountHolderPendingReward]:
    return (
        polaris_db_session.execute(select(AccountHolderPendingReward).where(campaign_slug == campaign_slug))
        .scalars()
        .all()
    )


def create_rewards_for_existing_account_holder(
    polaris_db_session: "Session",
    retailer_slug: str,
    reward_count: int,
    account_holder_id: int,
    reward_slug: Optional[str] = "reward-test-slug",
) -> None:
    rewards = []
    for count in range(1, int(reward_count) + 1):
        reward = AccountHolderReward(
            reward_uuid=str(uuid4()),
            code=f"reward-code-{count}",
            issued_date=datetime.now() - timedelta(days=1),
            expiry_date=datetime.now() + timedelta(days=1),
            status="ISSUED",
            reward_slug=reward_slug,
            retailer_slug=retailer_slug,
            idempotency_token=str(uuid4()),
            account_holder_id=account_holder_id,
        )
        rewards.append(reward)

    polaris_db_session.add_all(rewards)
    polaris_db_session.commit()


def create_pending_rewards_for_existing_account_holder(
    polaris_db_session: "Session",
    retailer_slug: str,
    count: int,
    account_holder_id: int,
    campaign_slug: str,
    reward_goal: int,
) -> None:
    for count in range(1, int(count) + 1):
        pending_reward = AccountHolderPendingReward(
            created_date=datetime.now() - timedelta(days=1),
            conversion_date=datetime.now() + timedelta(days=1),
            value=reward_goal,
            campaign_slug=campaign_slug,
            reward_slug=f"pending_reward-slug-{count}",
            retailer_slug=retailer_slug,
            account_holder_id=account_holder_id,
            idempotency_token=str(uuid4()),
        )
        polaris_db_session.add(pending_reward)

    polaris_db_session.commit()
