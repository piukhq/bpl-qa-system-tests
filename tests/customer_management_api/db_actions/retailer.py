from typing import TYPE_CHECKING

from db.polaris.models import RetailerConfig


if TYPE_CHECKING:
    from sqlalchemy.orm import Session

def get_retailer(polaris_db_session: "Session", slug: str) -> RetailerConfig:
    return polaris_db_session.query(RetailerConfig).filter_by(slug=slug).first()