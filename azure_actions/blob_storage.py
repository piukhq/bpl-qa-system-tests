import logging
import os

from datetime import datetime

from azure.core.exceptions import HttpResponseError
from azure.storage.blob import BlobClient, BlobType, ContentSettings

from db.carina.models import Reward
from settings import BLOB_IMPORT_CONTAINER, BLOB_STORAGE_DSN, logger


def put_new_reward_updates_file(
    retailer_slug: str, rewards: list[Reward], blob_name: str, reward_status: str
) -> BlobClient:
    blob_path = os.path.join(retailer_slug, "reward-updates", blob_name)
    today_date = datetime.now().strftime("%Y-%m-%d")
    content = "\n".join([f"{reward.code},{today_date},{reward_status}" for reward in rewards])
    logging.info(f"content of csv file upload: {content}")
    return upload_blob(blob_path, content)


def upload_blob(blob_path: str, content: str) -> BlobClient:
    content_binary = content.encode("utf-8")
    blob_client = BlobClient.from_connection_string(
        conn_str=BLOB_STORAGE_DSN,
        container_name=BLOB_IMPORT_CONTAINER,
        blob_name=blob_path,
    )

    logger.info(f"Uploading {blob_path} to blob storage")
    try:
        blob_client.upload_blob(
            content_binary.decode(),  # type: ignore
            blob_type=BlobType.BlockBlob,
            overwrite=True,
            content_settings=ContentSettings(content_type="text/csv"),
        )
    except HttpResponseError as e:
        # This can happen: that Carina will be processing the test file at the exact same time
        logger.warning(f"Error while uploading {blob_path} to blob storage due to Carina owning the lease {str(e)}")
        pass

    return blob_client
