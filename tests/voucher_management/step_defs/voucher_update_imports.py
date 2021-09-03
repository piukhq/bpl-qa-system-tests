import logging
import uuid

from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Callable, List

from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.storage.blob import BlobServiceClient
from pytest_bdd import given, parsers, then
from sqlalchemy import Date
from sqlalchemy.future import select

from db.carina.models import Voucher, VoucherConfig, VoucherUpdate
from settings import BLOB_ARCHIVE_CONTAINER, BLOB_STORAGE_DSN, LOCAL

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


voucher_1_code = "TEST12345678"
voucher_2_code = "TEST87654321"
voucher_3_code = "TESTDELETED"


@given(parsers.parse("The voucher code provider provides a bulk file for {retailer_slug}"))
def voucher_updates_upload(
    retailer_slug: str,
    voucher_config: VoucherConfig,
    create_mock_voucher: Callable,
    upload_voucher_updates_to_blob_storage: Callable,
) -> None:
    """
    The fixture should place a CSV file onto blob storage, which a running instance of
    carina (the scheduler job for doing these imports) will pick up and process, putting rows into carina's DB
    for today's date.
    """
    # GIVEN
    voucher_1 = create_mock_voucher(
        voucher_config=voucher_config, **{"id": str(uuid.uuid4()), "voucher_code": voucher_1_code, "allocated": True}
    )
    voucher_2 = create_mock_voucher(
        voucher_config=voucher_config, **{"id": str(uuid.uuid4()), "voucher_code": voucher_2_code, "allocated": True}
    )
    voucher_3 = create_mock_voucher(
        voucher_config=voucher_config, **{"id": str(uuid.uuid4()), "voucher_code": voucher_3_code, "allocated": False}
    )
    url = upload_voucher_updates_to_blob_storage([voucher_1, voucher_2, voucher_3])

    assert url


def _get_voucher_update_rows(
    carina_db_session: "Session", retailer_slug: str, req_date: str, limit: int = 2
) -> List[VoucherUpdate]:
    """
    Get latest <limit> voucher_update rows matching a retailer and a date e.g. '2021-09-01'
    """
    voucher_update_rows = (
        carina_db_session.execute(
            select(VoucherUpdate)
            .where(VoucherUpdate.retailer_slug == retailer_slug, VoucherUpdate.updated_at.cast(Date) == req_date)
            .order_by(VoucherUpdate.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )

    return voucher_update_rows


@then(parsers.parse("the file for {retailer_slug} is imported by the voucher management system"))
def check_voucher_updates_import(
    retailer_slug: str,
    voucher_config: VoucherConfig,
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
    voucher_update_rows = []
    n_voucher_update_rows = 0
    for _ in range(wait_times):
        # wait for callback process to handle the callback
        logging.info(f"Sleeping for {wait_duration_secs} seconds...")
        sleep(wait_duration_secs)
        voucher_update_rows = _get_voucher_update_rows(carina_db_session, retailer_slug, today)
        if voucher_update_rows:
            n_voucher_update_rows = len(voucher_update_rows)
            break
        else:
            logging.info("Still waiting for Carina to process today's voucher update test file.")

    # THEN
    # Latest 2 rows should be the vouchers created in the initial Given part of this test
    logging.info(
        "checking that voucher_update table contains at least 2 voucher update rows for today's date, "
        f"found: {n_voucher_update_rows}"
    )
    assert n_voucher_update_rows == 2
    assert voucher_update_rows[0].voucher_code in [voucher_1_code, voucher_2_code]
    assert voucher_update_rows[1].voucher_code in [voucher_1_code, voucher_2_code]
    # Soft deleted vouchers should not appear in the voucher_update table
    assert voucher_update_rows[0].voucher_code not in [voucher_3_code]
    assert voucher_update_rows[1].voucher_code not in [voucher_3_code]


@then(
    parsers.parse(
        "the unallocated voucher for {retailer_slug} is marked as deleted and is not imported "
        "by the voucher management system"
    )
)
def check_voucher_updates_deleted(
    retailer_slug: str,
    voucher_config: VoucherConfig,
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
    for _ in range(wait_times):
        # wait for callback process to handle the callback
        logging.info(f"Sleeping for {wait_duration_secs} seconds...")
        sleep(wait_duration_secs)
        deleted_voucher_row = (
            carina_db_session.execute(
                select(Voucher).where(
                    Voucher.voucher_code == voucher_3_code,
                    Voucher.retailer_slug == retailer_slug,
                    Voucher.updated_at.cast(Date) == today,
                    Voucher.deleted.is_(True),
                )
            )
            .scalars()
            .first()
        )
        if deleted_voucher_row:
            break
        else:
            logging.info("Still waiting for Carina to process today's voucher delete.")

    # THEN
    logging.info(
        f"checking that voucher table contains single record for the deleted voucher code {voucher_3_code}, "
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

            try:
                lease = blob_client.acquire_lease(lease_duration=60)
            except HttpResponseError:
                logging.debug(f"Skipping blob {blob.name} as we could not acquire a lease.")
                continue
            else:
                byte_content = blob_client.download_blob(lease=lease).readall()
                assert byte_content
