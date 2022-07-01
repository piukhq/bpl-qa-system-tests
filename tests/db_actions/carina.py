from typing import TYPE_CHECKING

from sqlalchemy.future import select

from db.carina.models import FetchType, Retailer, Reward, RewardConfig

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_reward_config_id(
    carina_db_session: "Session",
    reward_slug: str,
) -> int:
    return carina_db_session.execute(
        select(RewardConfig.id).where(
            RewardConfig.reward_slug == reward_slug,
        )
    ).scalar_one()


def get_fetch_type_id(
    carina_db_session: "Session",
    fetch_type_name: str,
) -> int:
    return carina_db_session.execute(select(FetchType.id).where(FetchType.name == fetch_type_name)).scalar_one()


def get_retailer_id(
    carina_db_session: "Session",
    retailer_slug: str,
) -> int:
    return carina_db_session.execute(select(Retailer.id).where(Retailer.slug == retailer_slug)).scalar_one()


def get_rewards(carina_db_session: "Session", reward_config_id: int, allocated: bool) -> list[Reward]:
    rewards = (
        carina_db_session.execute(
            select(Reward).where(Reward.reward_config_id == reward_config_id, Reward.allocated.is_(allocated))
        )
        .scalars()
        .all()
    )
    return rewards
