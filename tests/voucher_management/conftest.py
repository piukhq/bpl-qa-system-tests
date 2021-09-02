from typing import TYPE_CHECKING, Callable, Dict, Generator, List

import pytest

from sqlalchemy import select

from azure_actions.blob_storage import upload_voucher_update_to_blob_storage
from db.carina.models import Voucher, VoucherConfig
from settings import BLOB_STORAGE_DSN, logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture(scope="function")
def upload_voucher_updates_to_blob_storage() -> Callable:
    def _upload_voucher_updates_to_blob_storage(vouchers: List[Voucher]) -> str:
        """Upload some voucher updates to blob storage to test end-to-end import"""
        url = ""

        if BLOB_STORAGE_DSN:
            retailer_slug = "test-retailer"
            logger.debug(f"Uploading voucher updates to blob storage for {retailer_slug}...")
            url = upload_voucher_update_to_blob_storage(retailer_slug, vouchers)
            logger.debug(f"Successfully uploaded voucher updates to blob storage: {url}")
        else:
            logger.debug("No BLOB_STORAGE_DSN set, skipping voucher updates upload")

        return url

    return _upload_voucher_updates_to_blob_storage


@pytest.fixture(scope="function")
def voucher_config(carina_db_session: "Session") -> VoucherConfig:
    voucher_config = (
        carina_db_session.execute(select(VoucherConfig).where(VoucherConfig.retailer_slug == "test-retailer"))
        .scalars()
        .first()
    )

    yield voucher_config


@pytest.fixture(scope="function")
def create_mock_voucher(carina_db_session: "Session") -> Generator:
    mock_vouchers = []

    def _create_mock_voucher(voucher_config: VoucherConfig, **voucher_params: Dict) -> Voucher:
        """
        Create a voucher in carina's test DB
        :param voucher_params: override any values for voucher
        :return: Callable function
        """
        default_voucher_params = {
            "voucher_code": "TSTCD1234",
            "retailer_slug": voucher_config.retailer_slug,
            "voucher_config": voucher_config,
            "allocated": False,
            "deleted": False,
        }

        assert voucher_params["id"], "You will need to pass in a new id for each mock Voucher"
        default_voucher_params.update(voucher_params)  # type: ignore
        mock_voucher = Voucher(**default_voucher_params)
        mock_vouchers.append(mock_voucher)
        carina_db_session.add(mock_voucher)
        carina_db_session.commit()

        return mock_voucher

    yield _create_mock_voucher

    for mock_voucher in mock_vouchers:
        carina_db_session.delete(mock_voucher)

    carina_db_session.commit()
