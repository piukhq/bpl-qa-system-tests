from db.models import Retailer
from db.session import SessionMaker


def get_retailer(slug: str) -> Retailer:
    with SessionMaker() as db_session:
        retailer = db_session.query(Retailer).filter_by(slug=slug).first()
        return retailer
