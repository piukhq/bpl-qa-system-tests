from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy.future import select

from db.polaris.models import (
    AccountHolder,
    AccountHolderCampaignBalance,
    AccountHolderPendingReward,
    AccountHolderReward,
)
from db.vela.models import Campaign

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_account_holder_for_retailer(polaris_db_session: "Session", retailer_id: int) -> AccountHolder:
    return polaris_db_session.execute(select(AccountHolder).where(retailer_id == retailer_id)).scalar_one()


def get_account_holder_with_email(polaris_db_session: "Session", email: str, retailer_id: int) -> AccountHolder:
    return polaris_db_session.execute(
        select(AccountHolder).where(email == email, retailer_id == retailer_id)
    ).scalar_one()


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
    account_holder: AccountHolder,
    campaign_slug: str,
) -> list[AccountHolderPendingReward]:
    return (
        polaris_db_session.execute(
            select(AccountHolderPendingReward).where(
                campaign_slug == campaign_slug, AccountHolderPendingReward.account_holder_id == account_holder.id
            )
        )
        .scalars()
        .all()
    )


def get_ordered_pending_rewards(
    polaris_db_session: "Session", account_holder: AccountHolder, campaign_slug: str
) -> list[AccountHolderPendingReward]:
    pending_rewards = get_pending_rewards(polaris_db_session, account_holder, campaign_slug)
    return sorted(
        pending_rewards,
        key=lambda x: x.created_at,
    )


def create_rewards_for_existing_account_holder(
    polaris_db_session: "Session",
    retailer_slug: str,
    reward_count: int,
    account_holder_id: int,
    reward_slug: str | None = "reward-test-slug",
    status: str = "ISSUED",
    expiry_date: datetime | None = None,
) -> None:
    rewards = []
    for _ in range(1, int(reward_count) + 1):
        reward = AccountHolderReward(
            reward_uuid=str(uuid4()),
            code=str(uuid4()),
            issued_date=datetime.now() - timedelta(days=1),
            expiry_date=expiry_date if expiry_date else datetime.now() + timedelta(days=1),
            status=status,
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
    num_rewards: int,
    account_holder_id: int,
    campaign_slug: str,
    reward_slug: str | None,
    reward_goal: int,
) -> None:
    count = 1
    for _ in range(int(num_rewards)):
        pending_reward = AccountHolderPendingReward(
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
        polaris_db_session.add(pending_reward)

    polaris_db_session.commit()


def create_pending_rewards_with_all_value_for_existing_account_holder(
    polaris_db_session: "Session",
    retailer_slug: str,
    conversion_date: date,
    prr_count: int,
    value: int,
    total_cost_to_user: int,
    account_holder_id: int,
    campaign_slug: str,
    reward_slug: str | None,
) -> AccountHolderPendingReward:

    pending_reward = AccountHolderPendingReward(
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
    polaris_db_session.add(pending_reward)

    polaris_db_session.commit()
    return pending_reward


def create_balance_for_account_holder(
    polaris_db_session: "Session", account_holder: AccountHolder, campaign: Campaign, balance: int = 0
) -> None:
    balance = AccountHolderCampaignBalance(account_holder_id=account_holder.id, campaign_slug=campaign.slug, balance=0)
    polaris_db_session.add(balance)
    polaris_db_session.commit()


def get_account_holder_balances_for_campaign(
    polaris_db_session: "Session", account_holders: list[AccountHolder], campaign_slug: str
) -> list[AccountHolderCampaignBalance]:
    return (
        polaris_db_session.execute(
            select(AccountHolderCampaignBalance).where(
                AccountHolderCampaignBalance.account_holder_id.in_([ah.id for ah in account_holders]),
                AccountHolderCampaignBalance.campaign_slug == campaign_slug,
            )
        )
        .scalars()
        .all()
    )
