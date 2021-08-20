import logging

from datetime import datetime
from typing import TYPE_CHECKING

from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.storage.blob import BlobServiceClient
from pytest_bdd import given, parsers, scenarios, then
from sqlalchemy import Date

from db.carina.models import VoucherConfig, VoucherUpdate
from settings import BLOB_ARCHIVE_CONTAINER, BLOB_STORAGE_DSN, LOCAL

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

scenarios("voucher_management/imports/")


@given(
    parsers.parse(
        "The voucher code provider provides a bulk file for {retailer_slug} and the file is "
        "imported by the voucher management system"
    )
)
def check_voucher_updates_import(retailer_slug: str, carina_db_session: "Session") -> None:
    """
    The schedule.run_test() function should place a CSV file onto blob storage, which a running instance of
    carina will pick up and process, putting rows into carina's DB for today's date. If you're running locally
    then assume those things will not be happening. Change your LOCAL setting if you want to test this.
    """
    if LOCAL:
        pass
    else:
        today: str = datetime.now().strftime("%Y-%m-%d")
        count_voucher_updates = (
            carina_db_session.query(VoucherUpdate)
            .join(VoucherConfig)
            .filter(VoucherUpdate.updated_at.cast(Date) == today)
            .filter(VoucherConfig.retailer_slug == retailer_slug)
            .count()
        )
        logging.info(
            "checking that voucher_update table contains at least 1 voucher update row for today's date, "
            f"found: {count_voucher_updates}"
        )
        assert count_voucher_updates >= 1


@then(parsers.parse("The {retailer_slug} import file is archived by the voucher importer"))
def check_voucher_updates_archive(retailer_slug: str, carina_db_session: "Session", request_context: dict) -> None:
    """
    The schedule.run_test() function should place a CSV file onto blob storage, which a running instance of
    carina will pick up and process, creating an archive blob for today's date. If you're running locally
    then assume those things will not be happening. Change your LOCAL setting if you want to test this.
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
