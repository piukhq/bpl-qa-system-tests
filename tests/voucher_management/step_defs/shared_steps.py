import logging

from datetime import datetime, timedelta
from time import sleep
from typing import Literal, Union

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient
from pytest_bdd import parsers, then

from settings import BLOB_ARCHIVE_CONTAINER, BLOB_STORAGE_DSN, BLOB_ERROR_CONTAINER


@then(parsers.parse("the file is moved to the {container_type} container by the voucher importer"))
def check_file_moved(
    container_type: Union[Literal["archive"], Literal["error"]],
    request_context: dict,
) -> None:
    blob_service_client = BlobServiceClient.from_connection_string(BLOB_STORAGE_DSN)
    now = datetime.now()
    # Note: possible timing issue with looking for %H%M (hour/minute) if test is behind or ahead of file_agent.py
    possible_dates = [now - timedelta(seconds=60), now, now + timedelta(seconds=60)]
    blob_starts_withs = [f"{dt.strftime('%Y/%m/%d/%H%M')}/{request_context['blob'].blob_name}" for dt in possible_dates]

    blob_container = None
    if container_type == "archive":
        blob_container = BLOB_ARCHIVE_CONTAINER
    elif container_type == "errors":
        blob_container = BLOB_ERROR_CONTAINER

    try:
        blob_service_client.create_container(blob_container)
    except ResourceExistsError:
        pass  # this is fine

    container = blob_service_client.get_container_client(blob_container)
    for i in range(7):
        if i:
            logging.info("No blobs found. Sleeping for 10 seconds...")
            sleep(10)
        logging.info(f"Looking for blobs on these paths: {blob_starts_withs}")
        blobs = []
        for blob_starts_with in blob_starts_withs:
            blobs.extend(list(container.list_blobs(name_starts_with=blob_starts_with)))

        if not blobs:
            continue
        else:
            logging.info("Found it!")
            break

    assert len(blobs) == 1

    container.delete_blob(blobs[0])
