from time import sleep
from typing import Union, TYPE_CHECKING

from db.models import AccountHolder, AccountHolderProfile, Retailer
from db.session import SessionMaker

if TYPE_CHECKING:
    from uuid import UUID
    from sqlalchemy.orm import Session


def get_account_holder(db_session: "Session", email: str, retailer: Union[str, Retailer]) -> AccountHolder:
    if isinstance(retailer, str):
        retailer = db_session.query(Retailer).filter_by(slug=retailer).first()

    return db_session.query(AccountHolder).filter_by(email=email, retailer=retailer).first()


def get_account_holder_by_id(db_session: "Session", account_holder_id: "UUID") -> AccountHolder:
    return db_session.query(AccountHolder).get(account_holder_id)


def get_active_account_holder(db_session: "Session", email: str, retailer: Union[str, Retailer]) -> AccountHolder:
    if isinstance(retailer, str):
        retailer = db_session.query(Retailer).filter_by(slug=retailer).first()

    account_holder = db_session.query(AccountHolder).filter_by(email=email, retailer=retailer).first()

    for i in range(1, 3):
        if account_holder.account_number is not None:
            break

        sleep(i)
        db_session.refresh(account_holder)

    return account_holder


def get_account_holder_profile(db_session: "Session", account_holder_id: str) -> AccountHolderProfile:
    return db_session.query(AccountHolderProfile).filter_by(account_holder_id=account_holder_id).first()


def assert_enrol_request_body_with_account_holder_table(
    account_holder: AccountHolder, request_body: dict, retailer_id: int
) -> None:
    account_holder_request_info = {"email": request_body["credentials"]["email"], "retailer_id": retailer_id}

    for field, request_value in account_holder_request_info.items():
        assert getattr(account_holder, field) == request_value


def assert_enrol_request_body_with_account_holder_profile_table(
    account_holder_profile: AccountHolderProfile, request_body: dict
) -> None:
    # commented out db_actions fields that arent getting saved yet on the prototype
    account_holder_profile_request_info = {
        "first_name": request_body["credentials"]["first_name"],
        "last_name": request_body["credentials"]["last_name"],
        # "birth_date": request_body["credentials"]["date_of_birth"],
        "phone": request_body["credentials"]["phone"],
        # "address_1": request_body["credentials"]["address_1"],
        # "address_2": request_body["credentials"]["address_2"],
        "postcode": request_body["credentials"]["postcode"],
        "city": request_body["credentials"]["city"],
        # "country": request_body["credentials"]["country"],
    }

    for field, request_value in account_holder_profile_request_info.items():
        assert getattr(account_holder_profile, field) == request_value
