from typing import TYPE_CHECKING, List, Optional

from db.vela.models import Campaign, CampaignStatuses, RetailerRewards

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_retailer_rewards(vela_db_session: "Session", retailer_slug: str) -> Optional[RetailerRewards]:
    retailer = vela_db_session.query(RetailerRewards).filter_by(slug=retailer_slug).first()

    assert retailer
    return vela_db_session.query(RetailerRewards).filter_by(slug=retailer_slug).first()


def get_active_campaigns(vela_db_session: "Session", retailer_slug: str) -> List[Campaign]:
    retailer = get_retailer_rewards(vela_db_session, retailer_slug)

    return vela_db_session.query(Campaign).filter_by(retailer_rewards=retailer, status=CampaignStatuses.ACTIVE).all()


def get_non_active_campaigns(vela_db_session: "Session", retailer_slug: str) -> List[Campaign]:
    retailer = get_retailer_rewards(vela_db_session, retailer_slug)

    return (
        vela_db_session.query(Campaign)
        .filter(Campaign.retailer_rewards == retailer, Campaign.status != CampaignStatuses.ACTIVE)
        .all()
    )
