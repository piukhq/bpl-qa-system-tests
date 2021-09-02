import logging
import uuid

from datetime import datetime
from typing import TYPE_CHECKING, Callable, List

from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.storage.blob import BlobServiceClient
from pytest_bdd import given, parsers, then
from sqlalchemy import Date
from sqlalchemy.future import select

from db.carina.models import VoucherConfig, VoucherUpdate
from settings import BLOB_ARCHIVE_CONTAINER, BLOB_STORAGE_DSN, LOCAL

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


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
        voucher_config=voucher_config, **{"id": str(uuid.uuid4()), "voucher_code": "TEST12345678", "allocated": True}
    )
    voucher_2 = create_mock_voucher(
        voucher_config=voucher_config, **{"id": str(uuid.uuid4()), "voucher_code": "TEST87654321", "allocated": True}
    )
    url = upload_voucher_updates_to_blob_storage([voucher_1, voucher_2])

    assert url


def _get_voucher_update_rows(carina_db_session: "Session", retailer_slug: str, req_date: str) -> List[VoucherUpdate]:
    """
    Get latest 2 voucher_update rows matching a retailer and a date e.g. '2021-09-01'
    """
    voucher_update_rows = (
        carina_db_session.execute(
            select(VoucherUpdate)
            .where(VoucherUpdate.retailer_slug == retailer_slug, VoucherUpdate.updated_at.cast(Date) == req_date)
            .order_by(VoucherUpdate.created_at.desc())
            .limit(2)
        )
        .scalars()
        .all()
    )

    return voucher_update_rows


@given(parsers.parse("the file for {retailer_slug} is imported by the voucher management system"))
def check_voucher_updates_import(
    retailer_slug: str, voucher_config: VoucherConfig, carina_db_session: "Session"
) -> None:
    # GIVEN
    today: str = datetime.now().strftime("%Y-%m-%d")
    voucher_update_rows = _get_voucher_update_rows(carina_db_session, retailer_slug, today)
    n_voucher_update_rows = len(voucher_update_rows)

    # THEN
    # Latest 2 rows should be the vouchers created in the initial Given part of this test
    assert n_voucher_update_rows == 2
    assert voucher_update_rows[0].voucher_code in ["TEST12345678", "TEST87654321"]
    assert voucher_update_rows[1].voucher_code in ["TEST12345678", "TEST87654321"]

    logging.info(
        "checking that voucher_update table contains at least 2 voucher update rows for today's date, "
        f"found: {n_voucher_update_rows}"
    )


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
