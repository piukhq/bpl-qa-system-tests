from db.models import User, UserProfile
from db.session import SessionMaker


def get_user(uuid):
    with SessionMaker() as db_session:
        return db_session.query(User).get(uuid=uuid)


def get_user_profile(uuid):
    with SessionMaker() as db_session:
        return db_session.query(UserProfile).get(uuid=uuid)
