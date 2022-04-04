from typing import TYPE_CHECKING, Optional

from sqlalchemy.future import select

from db.polaris.models import AccountHolder, AccountHolderReward

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_account_holder(polaris_db_session: "Session", email: str, retailer_id: int) -> Optional[AccountHolder]:
    account_holder = polaris_db_session.execute(
        select(AccountHolder).where(email == email, retailer_id == retailer_id)
    ).one_or_none()
    return account_holder


def get_account_holder_reward(
    polaris_db_session: "Session", reward_slug: str, retailer_slug: str
) -> Optional[AccountHolderReward]:
    account_holder_reward = polaris_db_session.execute(
        select(AccountHolderReward).where(reward_slug == reward_slug, retailer_slug == retailer_slug)
    ).one_or_none()
    return account_holder_reward
