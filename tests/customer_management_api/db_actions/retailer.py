from typing import TYPE_CHECKING

from db.models import Retailer

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_retailer(db_session: "Session", slug: str) -> Retailer:
    return db_session.query(Retailer).filter_by(slug=slug).first()
