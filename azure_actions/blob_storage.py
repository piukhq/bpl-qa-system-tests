import logging
import os
import uuid

from datetime import datetime, timedelta
from time import sleep
from typing import Literal

from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.storage.blob import BlobClient, BlobProperties, BlobServiceClient, BlobType, ContainerClient, ContentSettings

from db.carina.models import Reward
from settings import (
    BLOB_ARCHIVE_CONTAINER,
    BLOB_ERROR_CONTAINER,
    BLOB_IMPORT_CONTAINER,
    BLOB_STORAGE_DSN,
    LOCAL,
    REPORT_CONTAINER,
    REPORT_DIRECTORY,
    logger,
)


def put_new_reward_updates_file(
    retailer_slug: str, rewards: list[Reward], blob_name: str, reward_status: str
) -> BlobClient:
    blob_path = os.path.join(retailer_slug, "rewards.update." + blob_name)
    today_date = datetime.now().strftime("%Y-%m-%d")
    content = "\n".join([f"{reward.code},{today_date},{reward_status}" for reward in rewards])
    logging.info(f"content of csv file upload: {content}\n Blob_path: {blob_path}")
    return upload_blob(blob_path, content)


def add_new_available_rewards_file(
    retailer_slug: str, codes: list[str], reward_slug: str, expired_date: str
) -> BlobClient:
    if expired_date is None:
        filename = ".".join([reward_slug, f"test_{uuid.uuid4()}.csv"])
    else:
        filename = ".".join([reward_slug, f"expires.{expired_date}.test_{uuid.uuid4()}.csv"])

    blob_name = ".".join(["rewards.import", filename])
    blob_path = os.path.join(retailer_slug, blob_name)
    content = "\n".join([code for code in codes])
    logging.info(f"content of csv file upload: {content}")
    return upload_blob(blob_path, content)


def upload_report_to_blob_storage(filename: str, blob_prefix: str = "bpl-auto") -> BlobClient:
    assert not LOCAL
    blob_name = f"{blob_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
    blob_path = os.path.join(REPORT_DIRECTORY, blob_name)
    logger.info(f"Uploading test report: {blob_path} to blob storage")
    blob = BlobClient.from_connection_string(
        conn_str=BLOB_STORAGE_DSN,
        container_name=REPORT_CONTAINER,
        blob_name=blob_path,
    )
    with open(filename, "rb") as f:
        blob.upload_blob(f, content_settings=ContentSettings(content_type="text/html"))  # type: ignore [attr-defined]

    return blob


def upload_blob(blob_path: str, content: str) -> BlobClient:
    blob_client = BlobClient.from_connection_string(
        conn_str=BLOB_STORAGE_DSN,
        container_name=BLOB_IMPORT_CONTAINER,
        blob_name=blob_path,
    )

    logger.info(f"Uploading {blob_path} to blob storage")
    try:
        blob_client.upload_blob(  # type: ignore [attr-defined]
            content,
            blob_type=BlobType.BlockBlob,
            overwrite=True,
            content_settings=ContentSettings(content_type="text/csv"),
        )
    except HttpResponseError as e:
        # This can happen: that Carina will be processing the test file at the exact same time
        logger.warning(f"Error while uploading {blob_path} to blob storage due to Carina owning the lease {str(e)}")
        pass

    return blob_client


def check_archive_blobcontainer(
    container_type: Literal["archive"] | Literal["error"],
) -> tuple[list[BlobProperties], ContainerClient]:
    blob_service_client: BlobServiceClient = BlobServiceClient.from_connection_string(BLOB_STORAGE_DSN)
    now = datetime.utcnow()
    # Note: possible timing issue with looking for %H%M (hour/minute) if test is behind or ahead of file_agent.py
    possible_dates = [now - timedelta(seconds=60), now, now + timedelta(seconds=60)]
    blob_starts_withs = [f"{dt.strftime('%Y/%m/%d/%H%M')}" for dt in possible_dates]

    # blob_container = None
    if container_type == "archive":
        blob_container = BLOB_ARCHIVE_CONTAINER
    elif container_type == "errors":
        blob_container = BLOB_ERROR_CONTAINER

    try:
        blob_service_client.create_container(blob_container)
    except ResourceExistsError:
        pass  # this is fine

    container = blob_service_client.get_container_client(blob_container)
    for i in range(10):
        logging.info("Sleeping for 10 seconds...")
        sleep(10)
        logging.info(f"Looking for blobs on these paths: {blob_starts_withs}")
        blobs = []
        for blob_starts_with in blob_starts_withs:
            blobs.extend(list(container.list_blobs(name_starts_with=blob_starts_with)))

        if not blobs:
            logging.info("No blobs found")
            continue
        else:
            logging.info("Found it!")
            break
    return blobs, container
