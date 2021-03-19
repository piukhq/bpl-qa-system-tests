from db.models import AccountHolder, AccountHolderProfile, Retailer
from db.session import SessionMaker


def get_account_holder(email: str, retailer_slug: str):
    with SessionMaker() as db_session:
        retailer = db_session.query(Retailer).filter_by(slug=retailer_slug).first()
        return db_session.query(AccountHolder).filter_by(email=email, retailer=retailer).first()


def get_user_profile(uuid: str):
    with SessionMaker() as db_session:
        return db_session.query(AccountHolderProfile).get(uuid=uuid)
