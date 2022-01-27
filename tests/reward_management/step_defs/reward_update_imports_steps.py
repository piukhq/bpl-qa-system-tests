import logging

from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Callable, List, Optional

from pytest_bdd import given, then
from pytest_bdd.parsers import parse
from sqlalchemy import Date
from sqlalchemy.future import select

from db.carina.models import Rewards, RewardConfig, RewardFileLog, RewardUpdate
from db.polaris.models import AccountHolderReward
from enums import FileAgentType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _get_reward_update_rows(carina_db_session: "Session", codes: List[str], req_date: str) -> List[RewardUpdate]:
    """
    Get reward_update rows matching code and a date e.g. '2021-09-01'
    """
    reward_update_rows = (
        carina_db_session.execute(
            select(RewardUpdate)
            .join(Rewards)
            .where(
                Rewards.code.in_(codes),
                RewardUpdate.updated_at.cast(Date) == req_date,
            )
        )
        .scalars()
        .all()
    )

    return reward_update_rows


def _get_reward_row(carina_db_session: "Session", code: str, req_date: str, deleted: bool) -> Rewards:
    return (
        carina_db_session.execute(
            select(Rewards).where(
                Rewards.code == code,
                Rewards.updated_at.cast(Date) == req_date,
                Rewards.deleted.is_(deleted),
            )
        )
        .scalars()
        .first()
    )


def _get_reward_file_log(
    carina_db_session: "Session", file_name: str, file_agent_type: FileAgentType
) -> Optional[RewardFileLog]:
    return (
        carina_db_session.execute(
            select(RewardFileLog).where(
                RewardFileLog.file_name == file_name, RewardFileLog.file_agent_type == file_agent_type.name
            )
        )
        .scalars()
        .one_or_none()
    )


@given(parse("The reward code provider provides a bulk update file for {retailer_slug}"))
def reward_updates_upload(
    retailer_slug: str,
    get_reward_config: Callable[[str, str], RewardConfig],
    create_mock_rewards: Callable,
    request_context: dict,
    upload_reward_updates_to_blob_storage: Callable,
) -> None:
    """
    The fixture should place a CSV file onto blob storage, which a running instance of
    carina (the scheduler job for doing these imports) will pick up and process, putting rows into carina's DB
    for today's date.
    """
    # GIVEN
    mock_rewards: List[Rewards] = create_mock_rewards(
        reward_config=get_reward_config(retailer_slug, "10percentoff"),
        n_rewards=3,
        reward_overrides=[
            {"allocated": True},
            {"allocated": True},
            {"allocated": False},  # This one should end up being soft-deleted
        ],
    )
    blob = upload_reward_updates_to_blob_storage(retailer_slug=retailer_slug, rewards=mock_rewards)
    assert blob
    request_context["mock_rewards"] = mock_rewards
    request_context["blob"] = blob


@given(parse("The reward code provider provides a bulk update file named {blob_name} for {retailer_slug}"))
def reward_updates_upload_blob_name(
    blob_name: str,
    retailer_slug: str,
    get_reward_config: Callable[[str, str], RewardConfig],
    create_mock_rewards: Callable,
    request_context: dict,
    upload_reward_updates_to_blob_storage: Callable,
) -> None:
    """
    The fixture should place a CSV file onto blob storage, which a running instance of
    carina (the scheduler job for doing these imports) will pick up and process, putting rows into carina's DB
    for today's date.
    """
    # GIVEN
    mock_rewards: List[Rewards] = create_mock_rewards(
        reward_config=get_reward_config(retailer_slug, "10percentoff"),
        n_rewards=3,
        reward_overrides=[
            {"allocated": True},
            {"allocated": True},
            {"allocated": False},  # This one should end up being soft-deleted
        ],
    )

    blob = upload_reward_updates_to_blob_storage(retailer_slug=retailer_slug, rewards=mock_rewards, blob_name=blob_name)

    assert blob
    request_context["mock_rewards"] = mock_rewards
    request_context["blob"] = blob


@given(parse("a {file_agent_type} reward file log record exists for the file name {file_name}"))
def check_for_reward_file_log(
    file_agent_type: str,
    file_name: str,
    request_context: dict,
    create_mock_reward_file_log: Callable,
    carina_db_session: "Session",
) -> None:
    """Check that one either exists, or create a mock"""
    if not _get_reward_file_log(
        carina_db_session=carina_db_session, file_name=file_name, file_agent_type=FileAgentType(file_agent_type)
    ):
        create_mock_reward_file_log(file_name=file_name, file_agent_type=FileAgentType(file_agent_type))


@then(parse("the file for {retailer_slug} is imported by the reward management system"))
def check_reward_updates_import(
    retailer_slug: str,
    request_context: dict,
    carina_db_session: "Session",
) -> None:
    """
    Wait for just over 1 min to give Carina a chance to process the test reward update file we've put
    onto blob storage
    """
    # GIVEN
    wait_times = 7
    wait_duration_secs = 10
    today: str = datetime.now().strftime("%Y-%m-%d")
    # The allocated reward codes created in step one
    reward_codes = [
        mock_reward.code for mock_reward in request_context["mock_rewards"] if mock_reward.allocated is True
    ]
    reward_update_rows = []
    for _ in range(wait_times):
        # wait for callback process to handle the callback
        logging.info(f"Sleeping for {wait_duration_secs} seconds...")
        sleep(wait_duration_secs)
        reward_update_rows = _get_reward_update_rows(carina_db_session, reward_codes, today)
        if reward_update_rows:
            break
        else:
            logging.info("Still waiting for Carina to process today's reward update test file.")

    # THEN
    # Two rows should be the allocated reward created from the initial Given part of this test
    n_reward_update_rows = len(reward_update_rows)
    logging.info(
        "checking that reward_update table contains 2 reward update rows for today's date, "
        f"found: {n_reward_update_rows}"
    )
    assert n_reward_update_rows == 2
    # Check that the allocated reward have not been marked for soft-deletion
    for reward_code in reward_codes:
        reward_row = _get_reward_row(
            carina_db_session=carina_db_session, code=reward_code, req_date=today, deleted=False
        )
        assert reward_row

    request_context["reward_update_rows"] = reward_update_rows


# fmt: off
@then(parse("the unallocated reward for {retailer_slug} is marked as deleted and is not imported by the reward management system"))  # noqa: E501
# fmt: on
def check_reward_updates_are_soft_deleted(
    retailer_slug: str,
    request_context: dict,
    carina_db_session: "Session",
) -> None:
    """
    Wait for just over 1 min to give Carina a chance to process the test reward update file we've put
    onto blob storage
    """
    # GIVEN
    wait_times = 7
    wait_duration_secs = 10
    today: str = datetime.now().strftime("%Y-%m-%d")
    deleted_reward_row = None
    reward_code = request_context["mock_rewards"][2].code  # The unallocated reward created in step one
    for _ in range(wait_times):
        deleted_reward_row = _get_reward_row(
            carina_db_session=carina_db_session, code=reward_code, req_date=today, deleted=True
        )
        if deleted_reward_row:
            break
        else:
            # Sleep after the check here as Carina will most likely have run already for previous steps,
            # but this test can still be run independently.
            logging.info(f"Sleeping for {wait_duration_secs} seconds...")
            sleep(wait_duration_secs)

    # THEN
    logging.info(
        f"checking that reward table contains a record for the deleted reward code {reward_code}, "
        f"for today's date, found one: {'true' if deleted_reward_row else 'false'}"
    )
    assert deleted_reward_row


@then("the status of the allocated account holder rewards is updated")
def check_account_holder_reward_statuses(request_context: dict, polaris_db_session: "Session") -> None:
    allocated_reward_codes = [reward.code for reward in request_context["mock_rewards"] if reward.allocated]
    account_holder_rewards = (
        polaris_db_session.execute(
            select(AccountHolderReward).where(
                AccountHolderReward.code.in_(allocated_reward_codes),
                AccountHolderReward.retailer_slug == "test-retailer",
            )
        )
        .scalars()
        .all()
    )

    assert len(allocated_reward_codes) == len(account_holder_rewards)

    for account_holder_reward in account_holder_rewards:
        for i in range(6):
            sleep(i)
            polaris_db_session.refresh(account_holder_reward)
            if account_holder_reward.status != "ISSUED":
                break

        assert account_holder_reward.status == "REDEEMED"
