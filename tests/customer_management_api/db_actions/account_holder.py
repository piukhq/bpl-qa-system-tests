from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Optional, Union

from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from db.polaris.models import AccountHolder, AccountHolderProfile, AccountHolderVoucher, RetailerConfig

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def get_account_holder(
    polaris_db_session: "Session", email: str, retailer: Union[str, RetailerConfig]
) -> Optional[AccountHolder]:
    if isinstance(retailer, str):
        retailer = polaris_db_session.query(RetailerConfig).filter_by(slug=retailer).first()

    return polaris_db_session.query(AccountHolder).filter_by(email=email, retailer_config=retailer).first()


def get_account_holder_by_id(polaris_db_session: "Session", account_holder_id: "UUID") -> AccountHolder:

    account_holder = (
        polaris_db_session.execute(
            select(AccountHolder)
            .options(joinedload(AccountHolder.account_holder_campaign_balance_collection))
            .where(AccountHolder.id == account_holder_id)
        )
        .scalars()
        .first()
    )

    if account_holder is None:
        raise ValueError(f"No account holder found for id {account_holder_id}.")

    return account_holder


def get_active_account_holder(
    polaris_db_session: "Session", email: str, retailer_slug: Union[str, RetailerConfig]
) -> AccountHolder:
    if isinstance(retailer_slug, str):
        retailer = polaris_db_session.query(RetailerConfig).filter_by(slug=retailer_slug).first()
        if retailer is None:
            raise ValueError(f"No retailer found for slug {retailer}.")
    else:
        retailer = retailer_slug

    account_holder = polaris_db_session.query(AccountHolder).filter_by(email=email, retailer_config=retailer).first()
    if account_holder is None:
        raise ValueError(f"No account holder found for email {email} and retailer {retailer.slug}.")

    for i in range(1, 3):
        if account_holder and account_holder.account_number is not None:
            break

        sleep(i)
        polaris_db_session.refresh(account_holder)

    return account_holder


def get_account_holder_profile(
    polaris_db_session: "Session", account_holder_id: int
) -> Union[AccountHolderProfile, None]:
    account_holder_profile = None

    # Give Polaris a chance to commit the record
    for i in range(1, 3):
        account_holder_profile = (
            polaris_db_session.query(AccountHolderProfile).filter_by(account_holder_id=account_holder_id).first()
        )
        if account_holder_profile:
            break
        else:
            sleep(i)

    # This will raise an exception if account_holder_profile is still None
    polaris_db_session.refresh(account_holder_profile)

    return account_holder_profile


def assert_enrol_request_body_with_account_holder_table(
    account_holder: AccountHolder, request_body: dict, retailer_id: int
) -> None:
    account_holder_request_info = {"email": request_body["credentials"]["email"], "retailer_id": retailer_id}

    for field, request_value in account_holder_request_info.items():
        value = getattr(account_holder, field)
        if field == "id":
            value = str(value)

        assert value == request_value


def assert_enrol_request_body_with_account_holder_profile_table(
    account_holder_profile: AccountHolderProfile, request_body: dict
) -> None:
    # commented out db_actions fields that arent getting saved yet on the prototype
    account_holder_profile_request_info = {
        "first_name": request_body["credentials"]["first_name"],
        "last_name": request_body["credentials"]["last_name"],
        "date_of_birth": datetime.strptime(request_body["credentials"]["date_of_birth"], "%Y-%m-%d").date(),
        "phone": request_body["credentials"].get("phone"),
        "address_line1": request_body["credentials"].get("address_line1"),
        "address_line2": request_body["credentials"].get("address_line2"),
        "postcode": request_body["credentials"].get("postcode"),
        "city": request_body["credentials"].get("city"),
        # "country": request_body["credentials"].get("country"),
    }

    for field, request_value in account_holder_profile_request_info.items():
        assert (
            getattr(account_holder_profile, field) == request_value
        ), f"Failed to match field {field} to {request_value}"


def get_account_holder_voucher(
    polaris_db_session: "Session", voucher_code: str, retailer_slug: str
) -> AccountHolderVoucher:
    voucher = (
        polaris_db_session.query(AccountHolderVoucher)
        .filter_by(
            # FIXME: BPL-190 will add a unique constraint across voucher_code and retailer at which point this query
            # should probably be updated to filter by retailer too to ensure the correct voucher is retrieved
            voucher_code=voucher_code
        )
        .first()
    )
    return voucher
