import logging
import uuid

from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Callable, List, Optional

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient
from pytest_bdd import given, parsers, then
from sqlalchemy.future import select  # type: ignore

from db.carina.models import VoucherConfig, Voucher
from settings import BLOB_ARCHIVE_CONTAINER, BLOB_STORAGE_DSN

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@given(
    parsers.parse("{retailer_slug} provides a csv file in the correct format for the {voucher_type_slug} voucher type")
)
def put_new_vouchers_file(
    retailer_slug: str,
    voucher_type_slug: str,
    get_voucher_config: Callable[[str], VoucherConfig],
    request_context: dict,
    create_mock_vouchers: Callable,
    upload_available_vouchers_to_blob_storage: Callable,
) -> None:
    pre_existing_vouchers: List[Voucher] = create_mock_vouchers(
        voucher_config=get_voucher_config(retailer_slug),
        n_vouchers=3,
        voucher_overrides=[
            {"allocated": True},
            {"allocated": False},
            {"allocated": False, "deleted": True},
        ],
    )
    new_voucher_codes = request_context["new_voucher_codes"] = [str(uuid.uuid4()) for _ in range(5)]
    pre_existing_voucher_codes = request_context["pre_existing_voucher_codes"] = [
        v.voucher_code for v in pre_existing_vouchers
    ]
    url = upload_available_vouchers_to_blob_storage(
        retailer_slug, new_voucher_codes + pre_existing_voucher_codes, voucher_type_slug=voucher_type_slug
    )
    assert url


@then("only unseen vouchers are imported by the voucher management system")
def check_new_vouchers_imported(request_context: dict, carina_db_session: "Session") -> None:
    new_codes = request_context["new_voucher_codes"]
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

    expected_codes = sorted(request_context["new_voucher_codes"] + request_context["pre_existing_voucher_codes"])
    db_codes = [v.voucher_code for v in vouchers] if vouchers else None
    assert expected_codes == db_codes


@then(parsers.parse("the {retailer_slug} voucher import file is archived by the voucher importer"))
def check_import_file_archived(request_context: dict, retailer_slug: str) -> None:
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_DSN)
    try:
        blob_service_client.create_container(BLOB_ARCHIVE_CONTAINER)
    except ResourceExistsError:
        pass  # this is fine

    container = blob_service_client.get_container_client(BLOB_ARCHIVE_CONTAINER)
    for blob in container.list_blobs(
        name_starts_with=f"{datetime.now().strftime('%Y/%m/%d/%H%M')}/{retailer_slug}/available-vouchers"
    ):
        blob_client = blob_service_client.get_blob_client(BLOB_ARCHIVE_CONTAINER, blob.name)
        assert blob_client.exists()
