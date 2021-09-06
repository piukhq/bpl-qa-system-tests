import logging

from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Callable, List

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient
from pytest_bdd import given, parsers, then
from sqlalchemy import Date
from sqlalchemy.future import select

from db.carina.models import Voucher, VoucherConfig, VoucherUpdate
from settings import BLOB_ARCHIVE_CONTAINER, BLOB_STORAGE_DSN, LOCAL

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _get_voucher_update_rows(
    carina_db_session: "Session", voucher_codes: List[str], req_date: str
) -> List[VoucherUpdate]:
    """
    Get voucher_update rows matching voucher_code's and a date e.g. '2021-09-01'
    """
    voucher_update_rows = (
        carina_db_session.execute(
            select(VoucherUpdate).where(
                VoucherUpdate.voucher_code.in_(voucher_codes), VoucherUpdate.updated_at.cast(Date) == req_date
            )
        )
        .scalars()
        .all()
    )

    return voucher_update_rows


def _get_voucher_row(carina_db_session: "Session", voucher_code: str, req_date: str, deleted: bool) -> Voucher:
    return (
        carina_db_session.execute(
            select(Voucher).where(
                Voucher.voucher_code == voucher_code,
                Voucher.updated_at.cast(Date) == req_date,
                Voucher.deleted.is_(deleted),
            )
        )
        .scalars()
        .first()
    )


@given(parsers.parse("The voucher code provider provides a bulk update file for {retailer_slug}"))
def voucher_updates_upload(
    retailer_slug: str,
    voucher_config: VoucherConfig,
    create_mock_vouchers: Callable,
    request_context: dict,
    upload_voucher_updates_to_blob_storage: Callable,
) -> None:
    """
    The fixture should place a CSV file onto blob storage, which a running instance of
    carina (the scheduler job for doing these imports) will pick up and process, putting rows into carina's DB
    for today's date.
    """
    # GIVEN
    mock_vouchers: List[Voucher] = create_mock_vouchers(
        voucher_config=voucher_config,
        n_vouchers=3,
        voucher_overrides=[
            {"allocated": True},
            {"allocated": True},
            {"allocated": False},  # This one should end up being soft-deleted
        ],
    )
    url = upload_voucher_updates_to_blob_storage(mock_vouchers)
    assert url
    request_context["mock_vouchers"] = mock_vouchers


@then(parsers.parse("the file for {retailer_slug} is imported by the voucher management system"))
def check_voucher_updates_import(
    retailer_slug: str,
    request_context: dict,
    carina_db_session: "Session",
) -> None:
    """
    Wait for just over 1 min to give Carina a chance to process the test voucher update file we've put
    onto blob storage
    """
    # GIVEN
    wait_times = 7
    wait_duration_secs = 10
    today: str = datetime.now().strftime("%Y-%m-%d")
    # The allocated voucher codes created in step one
    voucher_codes = [
        mock_voucher.voucher_code for mock_voucher in request_context["mock_vouchers"] if mock_voucher.allocated is True
    ]
    voucher_update_rows = []
    for _ in range(wait_times):
        # wait for callback process to handle the callback
        logging.info(f"Sleeping for {wait_duration_secs} seconds...")
        sleep(wait_duration_secs)
        voucher_update_rows = _get_voucher_update_rows(carina_db_session, voucher_codes, today)
        if voucher_update_rows:
            break
        else:
            logging.info("Still waiting for Carina to process today's voucher update test file.")

    # THEN
    # Two rows should be the allocated vouchers created from the initial Given part of this test
    n_voucher_update_rows = len(voucher_update_rows)
    logging.info(
        "checking that voucher_update table contains 2 voucher update rows for today's date, "
        f"found: {n_voucher_update_rows}"
    )
    assert n_voucher_update_rows == 2
    # Check that the allocated vouchers have not been marked for soft-deletion
    for voucher_code in voucher_codes:
        voucher_row = _get_voucher_row(
            carina_db_session=carina_db_session, voucher_code=voucher_code, req_date=today, deleted=False
        )
        assert voucher_row

    request_context["voucher_update_rows"] = voucher_update_rows


@then(
    parsers.parse(
        "the unallocated voucher for {retailer_slug} is marked as deleted and is not imported "
        "by the voucher management system"
    )
)
def check_voucher_updates_are_soft_deleted(
    retailer_slug: str,
    request_context: dict,
    carina_db_session: "Session",
) -> None:
    """
    Wait for just over 1 min to give Carina a chance to process the test voucher update file we've put
    onto blob storage
    """
    # GIVEN
    wait_times = 7
    wait_duration_secs = 10
    today: str = datetime.now().strftime("%Y-%m-%d")
    deleted_voucher_row = None
    voucher_code = request_context["mock_vouchers"][2].voucher_code  # The unallocated voucher created in step one
    for _ in range(wait_times):
        deleted_voucher_row = _get_voucher_row(
            carina_db_session=carina_db_session, voucher_code=voucher_code, req_date=today, deleted=True
        )
        if deleted_voucher_row:
            break
        else:
            # Sleep after the check here as Carina will most likely have run already for previous steps,
            # but this test can still be run independently.
            logging.info("Still waiting for Carina to process today's unallocated vouchers.")
            logging.info(f"Sleeping for {wait_duration_secs} seconds...")
            sleep(wait_duration_secs)

    # THEN
    logging.info(
        f"checking that voucher table contains a record for the deleted voucher code {voucher_code}, "
        f"for today's date, found one: {'true' if deleted_voucher_row else 'false'}"
    )
    assert deleted_voucher_row


@then(parsers.parse("The {retailer_slug} import file is archived by the voucher importer"))
def check_voucher_updates_archive(retailer_slug: str, carina_db_session: "Session", request_context: dict) -> None:
    """
    The fixture should place a CSV file onto blob storage, which a running instance of
    carina (the scheduler job for doing these imports) will pick up and process, archiving on the carina-archive
    container for today's date
    """
    if LOCAL:
        pass
    else:
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_DSN)
        try:
            blob_service_client.create_container(BLOB_ARCHIVE_CONTAINER)
        except ResourceExistsError:
            pass  # this is fine

        container = blob_service_client.get_container_client(BLOB_ARCHIVE_CONTAINER)
        for blob in container.list_blobs(
            name_starts_with=f"{datetime.now().strftime('%Y/%m/%d')}/{retailer_slug}/voucher-updates"
        ):
            blob_client = blob_service_client.get_blob_client(BLOB_ARCHIVE_CONTAINER, blob.name)
            assert blob_client.exists()


@then(parsers.parse("the entries for today's date in the voucher_update table are cleaned up"))
def check_voucher_updates_deleted(
    request_context: dict,
    carina_db_session: "Session",
) -> None:
    """
    Clean up today's entries into the voucher_update table
    """
    # GIVEN
    today: str = datetime.now().strftime("%Y-%m-%d")
    voucher_update_rows = request_context["voucher_update_rows"]
    for voucher_update_row in voucher_update_rows:
        carina_db_session.delete(voucher_update_row)

    carina_db_session.commit()

    voucher_codes = [mock_voucher.voucher_code for mock_voucher in request_context["mock_vouchers"]]
    voucher_update_rows = _get_voucher_update_rows(carina_db_session, voucher_codes, today)
    assert not voucher_update_rows
