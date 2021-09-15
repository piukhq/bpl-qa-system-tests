import uuid

from datetime import datetime
from typing import TYPE_CHECKING, Callable, Dict, Generator, List

import pytest

from sqlalchemy.future import select

from azure_actions.blob_storage import upload_voucher_update_to_blob_storage
from db.carina.models import Voucher, VoucherConfig
from db.polaris.models import AccountHolder, AccountHolderVoucher, RetailerConfig
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
def mock_account_holder(polaris_db_session: "Session") -> AccountHolder:
    retailer_slug = "test-retailer"

    account_holder = (
        polaris_db_session.execute(
            select(AccountHolder)
            .join(RetailerConfig)
            .where(
                AccountHolder.email == "voucher_status_adjustment@automated.tests",
                RetailerConfig.slug == retailer_slug,
            )
        )
        .scalars()
        .first()
    )

    if account_holder is None:
        retailer_id = (
            polaris_db_session.execute(select(RetailerConfig.id).where(RetailerConfig.slug == retailer_slug))
            .scalars()
            .one()
        )

        account_holder = AccountHolder(
            id=uuid.uuid4(),
            email="voucher_status_adjustment@automated.tests",
            retailer_id=retailer_id,
            status="ACTIVE",
        )
        polaris_db_session.add(account_holder)
        polaris_db_session.commit()

    return account_holder


@pytest.fixture(scope="function")
def create_mock_vouchers(
    carina_db_session: "Session", polaris_db_session: "Session", mock_account_holder: AccountHolder
) -> Generator:
    mock_vouchers: List[Voucher] = []
    mock_account_holder_vouchers: List[AccountHolderVoucher] = []
    now = datetime.utcnow()

    def _create_mock_vouchers(voucher_config: VoucherConfig, n_vouchers: int, voucher_overrides: List[Dict]) -> Voucher:
        """
        Create a voucher in carina's test DB
        :param voucher_overrides: override any values for voucher, one for each voucher you require
        :return: Callable function
        """
        assert (
            len(voucher_overrides) == n_vouchers
        ), "You must pass in an (empty if necessary) override dict for each voucher"
        for idx in range(n_vouchers):
            voucher_params = {
                "id": str(uuid.uuid4()),
                "voucher_code": str(uuid.uuid4()),
                "retailer_slug": voucher_config.retailer_slug,
                "voucher_config": voucher_config,
                "allocated": False,
                "deleted": False,
            }

            voucher_params.update(voucher_overrides[idx])
            mock_voucher = Voucher(**voucher_params)
            carina_db_session.add(mock_voucher)
            mock_vouchers.append(mock_voucher)

            if voucher_params["allocated"]:
                mock_account_holder_voucher = AccountHolderVoucher(
                    account_holder_id=str(mock_account_holder.id),
                    voucher_id=voucher_params["id"],
                    voucher_code=voucher_params["voucher_code"],
                    issued_date=now,
                    status="ISSUED",
                    voucher_type_slug=voucher_config.voucher_type_slug,
                    retailer_slug=voucher_config.retailer_slug,
                )
                polaris_db_session.add(mock_account_holder_voucher)
                mock_account_holder_vouchers.append(mock_account_holder_voucher)

        carina_db_session.commit()
        polaris_db_session.commit()

        return mock_vouchers

    yield _create_mock_vouchers

    for voucher in mock_vouchers:
        carina_db_session.delete(voucher)

    carina_db_session.commit()

    for account_holder_voucher in mock_account_holder_vouchers:
        polaris_db_session.delete(account_holder_voucher)

    polaris_db_session.commit()
