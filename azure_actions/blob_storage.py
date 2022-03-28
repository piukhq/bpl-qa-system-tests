# import logging
# import os
# import uuid
#
# from datetime import datetime
# from typing import List, Optional
#
# from azure.core.exceptions import HttpResponseError
# from azure.storage.blob import BlobClient, BlobType, ContentSettings
#
# from db.carina.models import Reward
# from settings import BLOB_IMPORT_CONTAINER, BLOB_STORAGE_DSN, LOCAL, REPORT_CONTAINER, REPORT_DIRECTORY, logger


# def upload_report_to_blob_storage(filename: str, blob_prefix: str = "bpl") -> BlobClient:
#     assert not LOCAL
#     blob_name = f"{blob_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
#     blob_path = os.path.join(REPORT_DIRECTORY, blob_name)
#     logger.info(f"Uploading test report: {blob_path} to blob storage")
#     blob = BlobClient.from_connection_string(
#         conn_str=BLOB_STORAGE_DSN,
#         container_name=REPORT_CONTAINER,
#         blob_name=blob_path,
#     )
#     with open(filename, "rb") as f:
#         blob.upload_blob(f, content_settings=ContentSettings(content_type="text/html"))
#
#     return blob

#
# def put_new_reward_updates_file(retailer_slug: str, rewards: List[Reward], blob_name: str) -> BlobClient:
#     blob_path = os.path.join(retailer_slug, "reward-updates", blob_name)
#     today_date = datetime.now().strftime("%Y-%m-%d")
#     content = "\n".join([f"{reward.code},{today_date},redeemed" for reward in rewards])
#     return upload_blob(blob_path, content)
#
#
# def put_new_available_rewards_file(
#     retailer_slug: str, codes: List[str], reward_slug: Optional[str] = None
# ) -> BlobClient:
#     blob_name = f"test_import_{uuid.uuid4()}.csv"
#     path_elems = [retailer_slug, "available-rewards", blob_name]
#     if reward_slug:
#         path_elems.insert(2, reward_slug)
#     blob_path = os.path.join(*path_elems)
#     content = "\n".join([code for code in codes])
#     logging.info(f"content of csv file upload: {content}")
#     return upload_blob(blob_path, content)


# def upload_blob(blob_path: str, content: str) -> BlobClient:
#     content_binary = content.encode("utf-8")
#     blob = BlobClient.from_connection_string(
#         conn_str=BLOB_STORAGE_DSN,
#         container_name=BLOB_IMPORT_CONTAINER,
#         blob_name=blob_path,
#     )
#
#     logger.info(f"Uploading {blob_path} to blob storage")
#     try:
#         blob.upload_blob(
#             content_binary.decode(),
#             blob_type=BlobType.BlockBlob,
#             overwrite=True,
#             content_settings=ContentSettings(content_type="text/csv"),
#         )
#     except HttpResponseError as e:
#         # This can happen: that Carina will be processing the test file at the exact same time
#         logger.warning(f"Error while uploading {blob_path} to blob storage due to Carina owning the lease {str(e)}")
#         pass
#
#     return blob
