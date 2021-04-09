from typing import Union

from db.models import AccountHolder, AccountHolderProfile, Retailer
from db.session import SessionMaker


def get_account_holder(email: str, retailer: Union[str, Retailer]):
    with SessionMaker() as db_session:
        if isinstance(retailer, str):
            retailer = db_session.query(Retailer).filter_by(slug=retailer).first()

        return db_session.query(AccountHolder).filter_by(email=email, retailer=retailer).first()


def get_account_holder_profile(account_holder_id: str):
    with SessionMaker() as db_session:
        return db_session.query(AccountHolderProfile).filter_by(account_holder_id=account_holder_id).first()


def assert_enrol_request_body_with_account_holder_table(account_holder, request_body, retailer_id):
    account_holder_request_info = {
        "email": request_body["credentials"]["email"],
        "retailer_id": retailer_id
    }

    for field, request_value in account_holder_request_info.items():
        assert getattr(account_holder, field) == request_value


def assert_enrol_request_body_with_account_holder_profile_table(account_holder_profile, request_body):
    # commented out db fields that arent getting saved yet on the prototype
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
