from typing import TYPE_CHECKING

from sqlalchemy.future import select

from db.hubble.models import Activity

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_latest_activity_by_type(
    hubble_db_session: "Session",
    activity_type: str,
) -> Activity:
    return (
        hubble_db_session.execute(
            select(Activity).where(Activity.type == activity_type).order_by(Activity.created_at.desc())
        )
        .scalars()
        .first()
    )
