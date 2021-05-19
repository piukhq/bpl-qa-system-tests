import time

from typing import TYPE_CHECKING

from db.models import EnrolmentCallback

if TYPE_CHECKING:

    from sqlalchemy.orm import Session


def get_enrolment_callback(db_session: "Session", account_holder_id: str) -> EnrolmentCallback:
    for i in (1, 3, 5, 10):
        time.sleep(i)
        callback = db_session.query(EnrolmentCallback).filter_by(account_holder_id=account_holder_id).first()
        if callback:
            break
    return callback
