import logging
import uuid

from time import sleep
from typing import TYPE_CHECKING, Callable, List, Optional

from pytest_bdd import given, then
from pytest_bdd.parsers import parse
from sqlalchemy.future import select

from db.carina.models import Voucher, VoucherConfig

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@given(parse("{retailer_slug} has pre-existing vouchers for the {voucher_type_slug} voucher type"))
def make_pre_existing_vouchers(
    retailer_slug: str,
    voucher_type_slug: str,
    get_voucher_config: Callable[[str, str], VoucherConfig],
    create_mock_vouchers: Callable,
    request_context: dict,
) -> None:
    pre_existing_vouchers: List[Voucher] = create_mock_vouchers(
        voucher_config=get_voucher_config(retailer_slug, voucher_type_slug),
        n_vouchers=3,
        voucher_overrides=[
            {"allocated": True},
            {"allocated": False},
            {"allocated": False, "deleted": True},
        ],
    )
    request_context["pre_existing_voucher_codes"] = [v.voucher_code for v in pre_existing_vouchers]


@given(parse("{retailer_slug} provides a csv file in the correct format for the {voucher_type_slug} voucher type"))
def put_new_vouchers_file(
    retailer_slug: str,
    voucher_type_slug: str,
    request_context: dict,
    upload_available_vouchers_to_blob_storage: Callable,
) -> None:
    new_voucher_codes = request_context["import_file_new_voucher_codes"] = [str(uuid.uuid4()) for _ in range(5)]
    blob = upload_available_vouchers_to_blob_storage(
        retailer_slug,
        new_voucher_codes + request_context.get("pre_existing_voucher_codes", []),
        voucher_type_slug=voucher_type_slug,
    )
    assert blob
    request_context["blob"] = blob


@then("only unseen vouchers are imported by the voucher management system")
def check_new_vouchers_imported(request_context: dict, carina_db_session: "Session") -> None:
    new_codes = request_context["import_file_new_voucher_codes"]
    pre_existing_codes = request_context["pre_existing_voucher_codes"]
    vouchers: Optional[List[Voucher]] = None
    for i in range(7):
        logging.info("Sleeping for 10 seconds...")
        sleep(10)
        vouchers = (
            carina_db_session.execute(select(Voucher).where(Voucher.voucher_code.in_(new_codes + pre_existing_codes)))
            .scalars()
            .all()
        )
        if vouchers and len(vouchers) != len(new_codes + pre_existing_codes):
            logging.info("New voucher codes not found...")
            continue
        else:
            break

    expected_codes = sorted(
        request_context["import_file_new_voucher_codes"] + request_context["pre_existing_voucher_codes"]
    )
    db_codes = sorted([v.voucher_code for v in vouchers]) if vouchers else None
    assert expected_codes == db_codes


@then("the voucher codes are not imported")
def check_vouchers_not_imported(carina_db_session: "Session", request_context: dict) -> None:
    vouchers = (
        carina_db_session.execute(
            select(Voucher).where(Voucher.voucher_code.in_(request_context["import_file_new_voucher_codes"]))
        )
        .scalars()
        .all()
    )
    assert not vouchers
