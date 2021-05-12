from typing import TYPE_CHECKING

from db.models import RetailerConfig

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_retailer(db_session: "Session", slug: str) -> RetailerConfig:
    return db_session.query(RetailerConfig).filter_by(slug=slug).first()
