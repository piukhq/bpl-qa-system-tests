import uuid

from datetime import datetime
from typing import TYPE_CHECKING, Callable, Dict, Generator, List, Optional

import pytest

from sqlalchemy import delete
from sqlalchemy.future import select

from azure_actions.blob_storage import put_new_available_vouchers_file, put_new_voucher_updates_file
from db.carina.models import Voucher, VoucherConfig, VoucherFileLog
from db.polaris.models import AccountHolder, AccountHolderVoucher, RetailerConfig
from enums import FileAgentType
from settings import BLOB_STORAGE_DSN, logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture(scope="function", autouse=True)
def cleanup_imported_vouchers(carina_db_session: "Session", request_context: dict) -> Generator:

    yield

    if voucher_codes := request_context.get("import_file_new_voucher_codes", []):
        logger.info("Deleting newly imported Vouchers...")
        carina_db_session.execute(delete(Voucher).where(Voucher.id.in_(voucher_codes)))
        carina_db_session.commit()


@pytest.fixture(scope="function")
def upload_available_vouchers_to_blob_storage() -> Callable:
    def func(retailer_slug: str, voucher_codes: List[str], *, voucher_type_slug: Optional[str] = None) -> Optional[str]:
        """Upload some new voucher codes to blob storage to test end-to-end import"""
        blob = None

        if BLOB_STORAGE_DSN:
            logger.debug(
                f"Uploading voucher import file to blob storage for {retailer_slug} "
                f"(voucher type: {voucher_type_slug})..."
            )
            blob = put_new_available_vouchers_file(retailer_slug, voucher_codes, voucher_type_slug)
            logger.debug(f"Successfully uploaded new voucher codes to blob storage: {blob.url}")
        else:
            logger.debug("No BLOB_STORAGE_DSN set, skipping voucher updates upload")

        return blob

    return func


@pytest.fixture(scope="function")
def upload_voucher_updates_to_blob_storage() -> Callable:
    def func(retailer_slug: str, vouchers: List[Voucher], blob_name: str = None) -> Optional[str]:
        """Upload some voucher updates to blob storage to test end-to-end import"""
        blob = None
        if blob_name is None:
            blob_name = f"test_import_{uuid.uuid4()}.csv"

        if BLOB_STORAGE_DSN:
            logger.debug(f"Uploading voucher updates to blob storage for {retailer_slug}...")
            blob = put_new_voucher_updates_file(retailer_slug=retailer_slug, vouchers=vouchers, blob_name=blob_name)
            logger.debug(f"Successfully uploaded voucher updates to blob storage: {blob.url}")
        else:
            logger.debug("No BLOB_STORAGE_DSN set, skipping voucher updates upload")

        return blob

    return func


@pytest.fixture(scope="function")
def get_voucher_config(carina_db_session: "Session") -> Callable:
    def func(retailer_slug: str, voucher_type_slug: Optional[str] = None) -> VoucherConfig:
        query = select(VoucherConfig).where(VoucherConfig.retailer_slug == retailer_slug)
        if voucher_type_slug is not None:
            query = query.where(VoucherConfig.voucher_type_slug == voucher_type_slug)
        return carina_db_session.execute(query).scalars().first()

    return func


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

    def func(voucher_config: VoucherConfig, n_vouchers: int, voucher_overrides: List[Dict]) -> Voucher:
        """
        Create a voucher in carina's test DB
        :param voucher_config: the VoucherConfig to link the vouchers to
        :param n_vouchers: the number of vouchers to create
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
                    idempotency_token=str(uuid.uuid4()),
                )
                polaris_db_session.add(mock_account_holder_voucher)
                mock_account_holder_vouchers.append(mock_account_holder_voucher)

        carina_db_session.commit()
        polaris_db_session.commit()

        return mock_vouchers

    yield func

    # note that VoucherUpdates are cascade deleted when associated Vouchers are deleted
    for voucher in mock_vouchers:
        carina_db_session.delete(voucher)

    carina_db_session.commit()

    for account_holder_voucher in mock_account_holder_vouchers:
        polaris_db_session.delete(account_holder_voucher)

    polaris_db_session.commit()


@pytest.fixture(scope="function")
def create_mock_voucher_file_log(carina_db_session: "Session") -> Generator:
    mock_voucher_file_log: VoucherFileLog = None

    def func(file_name: str, file_agent_type: FileAgentType) -> VoucherFileLog:
        """
        Create a voucher file log in carina's test DB
        :param file_name: a blob file name (full path)
        :param file_agent_type: FileAgentType
        :return: Callable function
        """
        params = {
            "file_name": file_name,
            "file_agent_type": file_agent_type,
        }
        mock_voucher_file_log = VoucherFileLog(**params)
        carina_db_session.add(mock_voucher_file_log)
        carina_db_session.commit()

        return mock_voucher_file_log

    yield func

    if mock_voucher_file_log:
        carina_db_session.delete(mock_voucher_file_log)
        carina_db_session.commit()
