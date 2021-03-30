import logging
import os
from datetime import datetime

from azure.storage.blob import BlobClient, ContentSettings

from settings import BLOB_STORAGE_DSN, REPORT_CONTAINER, REPORT_DIRECTORY

logger = logging.getLogger(__name__)


def upload_report_to_blob_storage(filename: str, blob_prefix: str = "bpl") -> str:
    blob_name = f"{blob_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
    blob_path = os.path.join(REPORT_DIRECTORY, blob_name)
    logger.info(f"Uploading test report: {blob_path} to blob storage")
    blob = BlobClient.from_connection_string(
        conn_str=BLOB_STORAGE_DSN,
        container_name=REPORT_CONTAINER,
        blob_name=blob_path,
    )
    with open(filename, "rb") as f:
        blob.upload_blob(f, content_settings=ContentSettings(content_type="text/html"))

    return blob.url
