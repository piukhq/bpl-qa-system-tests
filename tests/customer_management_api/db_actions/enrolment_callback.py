import time
import uuid

from typing import TYPE_CHECKING, Union

from db.polaris.models import EnrolmentCallback

if TYPE_CHECKING:

    from sqlalchemy.orm import Session


def get_enrolment_callback(
    polaris_db_session: "Session", account_holder_id: Union[str, uuid.UUID]
) -> EnrolmentCallback:
    if isinstance(account_holder_id, uuid.UUID):
        account_holder_id = str(account_holder_id)

    for i in (1, 3, 5, 10):
        time.sleep(i)
        callback = polaris_db_session.query(EnrolmentCallback).filter_by(account_holder_id=account_holder_id).first()
        if callback:
            break
    return callback
