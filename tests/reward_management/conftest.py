import uuid

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Callable, Dict, Generator, List, Optional

import pytest

from sqlalchemy import delete
from sqlalchemy.future import select

from azure_actions.blob_storage import put_new_available_rewards_file, put_new_reward_updates_file
from db.carina.models import Rewards, RewardConfig, RewardFileLog
from db.polaris.models import AccountHolder, AccountHolderReward, RetailerConfig
from enums import FileAgentType
from settings import BLOB_STORAGE_DSN, logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture(scope="function", autouse=True)
def cleanup_imported_rewards(carina_db_session: "Session", request_context: dict) -> Generator:

    yield

    if reward_codes := request_context.get("import_file_new_reward_codes", []):
        logger.info("Deleting newly imported Rewards...")
        carina_db_session.execute(delete(Rewards).where(Rewards.id.in_(reward_codes)))
        carina_db_session.commit()


@pytest.fixture(scope="function")
def upload_available_rewards_to_blob_storage() -> Callable:
    def func(retailer_slug: str, codes: List[str], *, reward_slug: Optional[str] = None) -> Optional[str]:
        """Upload some new reward codes to blob storage to test end-to-end import"""
        blob = None

        if BLOB_STORAGE_DSN:
            logger.debug(
                f"Uploading reward import file to blob storage for {retailer_slug} " f"(reward slug: {reward_slug})..."
            )
            blob = put_new_available_rewards_file(retailer_slug, codes, reward_slug)
            logger.debug(f"Successfully uploaded new reward codes to blob storage: {blob.url}")
        else:
            logger.debug("No BLOB_STORAGE_DSN set, skipping reward updates upload")

        return blob

    return func


@pytest.fixture(scope="function")
def upload_reward_updates_to_blob_storage() -> Callable:
    def func(retailer_slug: str, rewards: List[Rewards], blob_name: str = None) -> Optional[str]:
        """Upload some reward updates to blob storage to test end-to-end import"""
        blob = None
        if blob_name is None:
            blob_name = f"test_import_{uuid.uuid4()}.csv"

        if BLOB_STORAGE_DSN:
            logger.debug(f"Uploading reward updates to blob storage for {retailer_slug}...")
            blob = put_new_reward_updates_file(retailer_slug=retailer_slug, rewards=rewards, blob_name=blob_name)
            logger.debug(f"Successfully uploaded reward updates to blob storage: {blob.url}")
        else:
            logger.debug("No BLOB_STORAGE_DSN set, skipping reward updates upload")

        return blob

    return func


@pytest.fixture(scope="function")
def get_reward_config(carina_db_session: "Session") -> Callable:
    def func(retailer_slug: str, reward_slug: Optional[str] = None) -> RewardConfig:
        query = select(RewardConfig).where(RewardConfig.retailer_slug == retailer_slug)
        if reward_slug is not None:
            query = query.where(RewardConfig.reward_slug == reward_slug)
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
                AccountHolder.email == "reward_status_adjustment@automated.tests",
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
            account_holder_uuid=uuid.uuid4(),
            email="reward_status_adjustment@automated.tests",
            retailer_id=retailer_id,
            status="ACTIVE",
        )
        polaris_db_session.add(account_holder)
        polaris_db_session.commit()

    return account_holder


@pytest.fixture(scope="function")
def create_mock_rewards(
    carina_db_session: "Session", polaris_db_session: "Session", mock_account_holder: AccountHolder
) -> Generator:
    mock_rewards: List[Rewards] = []
    mock_account_holder_rewards: List[AccountHolderReward] = []
    now = datetime.utcnow()

    def func(reward_config: RewardConfig, n_rewards: int, reward_overrides: List[Dict]) -> Rewards:
        """
        Create a reward in carina's test DB
        :param reward_config: the RewardConfig to link the rewards to
        :param n_rewards: the number of rewards to create
        :param reward_overrides: override any values for Reward, one for each reward you require
        :return: Callable function
        """
        assert (
            len(reward_overrides) == n_rewards
        ), "You must pass in an (empty if necessary) override dict for each reward"
        for idx in range(n_rewards):
            reward_params = {
                "id": str(uuid.uuid4()),
                "code": str(uuid.uuid4()),
                "retailer_slug": reward_config.retailer_slug,
                "reward_config": reward_config,
                "allocated": False,
                "deleted": False,
            }

            reward_params.update(reward_overrides[idx])
            mock_reward = Rewards(**reward_params)
            carina_db_session.add(mock_reward)
            mock_rewards.append(mock_reward)

            if reward_params["allocated"]:
                mock_account_holder_reward = AccountHolderReward(
                    account_holder_id=mock_account_holder.id,
                    reward_uuid=reward_params["id"],
                    code=reward_params["code"],
                    issued_date=now,
                    expiry_date=now + timedelta(days=30),
                    status="ISSUED",
                    reward_slug=reward_config.reward_slug,
                    retailer_slug=reward_config.retailer_slug,
                    idempotency_token=str(uuid.uuid4()),
                )
                polaris_db_session.add(mock_account_holder_reward)
                mock_account_holder_rewards.append(mock_account_holder_reward)

        carina_db_session.commit()
        polaris_db_session.commit()

        return mock_rewards

    yield func

    # note that RewardUpdates are cascade deleted when associated Rewards are deleted
    for reward in mock_rewards:
        carina_db_session.delete(reward)

    carina_db_session.commit()

    for account_holder_reward in mock_account_holder_rewards:
        polaris_db_session.delete(account_holder_reward)

    polaris_db_session.commit()


@pytest.fixture(scope="function")
def create_mock_reward_file_log(carina_db_session: "Session") -> Generator:
    mock_reward_file_log: RewardFileLog = None

    def func(file_name: str, file_agent_type: FileAgentType) -> RewardFileLog:
        """
        Create a reward file log in carina's test DB
        :param file_name: a blob file name (full path)
        :param file_agent_type: FileAgentType
        :return: Callable function
        """
        params = {
            "file_name": file_name,
            "file_agent_type": file_agent_type,
        }
        mock_reward_file_log = RewardFileLog(**params)
        carina_db_session.add(mock_reward_file_log)
        carina_db_session.commit()

        return mock_reward_file_log

    yield func

    if mock_reward_file_log:
        carina_db_session.delete(mock_reward_file_log)
        carina_db_session.commit()
