import json
import logging
import time

from datetime import datetime, timedelta, timezone
from time import sleep
from typing import TYPE_CHECKING, Any, Literal

from faker import Faker
from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse
from retry_tasks_lib.enums import RetryTaskStatuses
from sqlalchemy import func, select, sql

import settings

from azure_actions.blob_storage import check_archive_blobcontainer
from db.carina.models import Retailer, Reward, RewardConfig
from db.polaris.models import AccountHolder, AccountHolderPendingReward, AccountHolderReward, RetailerConfig
from db.vela.models import Campaign, CampaignStatuses
from tests.api.base import Endpoints
from tests.db_actions.carina import get_reward_config_id, get_rewards, get_rewards_by_reward_config
from tests.db_actions.polaris import (
    create_pending_rewards_with_all_value_for_existing_account_holder,
    get_account_holder_balances_for_campaign,
    get_account_holder_for_retailer,
    get_account_holder_reward,
    get_pending_reward_by_order,
    get_pending_rewards,
)
from tests.db_actions.retry_tasks import (
    get_latest_callback_task_for_account_holder,
    get_latest_task,
    get_retry_task_audit_data,
    get_tasks_by_type_and_key_value,
)
from tests.db_actions.reward import get_last_created_reward_issuance_task
from tests.db_actions.vela import get_campaign_status
from tests.requests.enrolment import (
    send_get_accounts,
    send_get_accounts_by_credential,
    send_number_of_accounts,
    send_number_of_accounts_by_post_credential,
)
from tests.requests.status_change import send_post_campaign_status_change
from tests.shared_utils.response_fixtures.errors import TransactionResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

scenarios("../features/trenette")
scenarios("../features/asos")

fake = Faker(locale="en_GB")


# CARINA CHECKS
@then(parse("the file is moved to the {container_type} container by the reward importer"))
def check_file_moved(
    container_type: Literal["archive"] | Literal["error"],
) -> None:
    blobs, container = check_archive_blobcontainer(container_type)

    assert len(blobs) == 1

    container.delete_blob(blobs[0])


@then(parse("rewards are allocated to the account holder for the {reward_slug} reward"))
def check_async_reward_allocation(carina_db_session: "Session", reward_slug: str) -> None:
    """Check that the reward in the Reward table has been marked as 'allocated' and that it has an id"""
    reward_config_id = get_reward_config_id(carina_db_session=carina_db_session, reward_slug=reward_slug)

    reward_allocation_task = get_last_created_reward_issuance_task(
        carina_db_session=carina_db_session, reward_config_id=reward_config_id
    )
    for i in range(20):
        time.sleep(i)
        carina_db_session.refresh(reward_allocation_task)
        if reward_allocation_task.status == RetryTaskStatuses.SUCCESS:
            break

    reward = carina_db_session.query(Reward).filter_by(id=reward_allocation_task.get_params()["reward_uuid"]).one()
    assert reward.allocated
    assert reward.id


@then(parse("all unallocated rewards for {reward_slug} reward config {are_arenot} soft deleted"))
def check_unallocated_rewards_deleted(
    carina_db_session: "Session",
    reward_slug: str,
    are_arenot: Literal["are"] | Literal["are not"],
) -> None:
    deleted = are_arenot == "are"
    reward_config_id = get_reward_config_id(carina_db_session, reward_slug)
    unallocated_rewards = get_rewards_by_reward_config(carina_db_session, reward_config_id, allocated=False)
    for i in range(5):
        time.sleep(i)  # Need to allow enough time for the task to soft delete rewards
        rewards_deleted = []
        for reward in unallocated_rewards:
            carina_db_session.refresh(reward)
            rewards_deleted.append(reward.deleted)

        if all(rewards_deleted) == deleted:
            break

    assert all(rewards_deleted) == deleted, f"All rewards are soft deleted as {deleted}"


@then(parse("the imported rewards are soft deleted"))
def reward_gets_soft_deleted(carina_db_session: "Session", imported_reward_ids: list[str]) -> None:
    rewards = get_rewards(carina_db_session, imported_reward_ids, allocated=True)
    for i in range(15):
        logging.info(f"Sleeping for {i} seconds...")
        sleep(i)  # Need to allow enough time for the task to soft delete rewards
        for reward in rewards:
            carina_db_session.refresh(reward)

        if all([reward.deleted for reward in rewards]):
            break
        logging.info("Not all rewards deleted yet...")

    assert all([reward.deleted for reward in rewards]), "All rewards not soft deleted"
    logging.info("All Rewards were soft deleted")


# fmt: off
@then(parse("there are {rewards_n:d} rewards for the {reward_slug} reward config, with allocated set to "
            "{allocation_status} and deleted set to {deleted_status}"))
# fmt: on
def check_rewards(
    carina_db_session: "Session",
    reward_slug: str,
    allocation_status: str,
    deleted_status: str,
    retailer_config: RetailerConfig,
    rewards_n: int,
) -> None:
    allocation_status_bool = allocation_status == "true"
    deleted_status_bool = deleted_status == "true"

    for i in range(10):
        logging.info(f"Sleeping for {i} seconds...")
        sleep(i)
        count = carina_db_session.execute(
            select(func.count("*"))
            .select_from(Reward)
            .join(Reward.rewardconfig)
            .join(Reward.retailer)
            .where(
                Reward.allocated.is_(allocation_status_bool),
                Reward.deleted.is_(deleted_status_bool),
                RewardConfig.reward_slug == reward_slug,
                Retailer.slug == retailer_config.slug,
            )
        ).scalar()
        if count == rewards_n:
            break
        logging.info(f"Reward count for query is {count}")
    assert count == rewards_n


@when(parse("the {reward_slug} reward config status has been updated to {status}"))
def check_reward_config_status(
    retailer_config: RetailerConfig, carina_db_session: "Session", reward_slug: str, status: str
) -> None:
    reward_config = carina_db_session.execute(
        select(RewardConfig)
        .join(Retailer)
        .where(Retailer.slug == retailer_config.slug, RewardConfig.reward_slug == reward_slug)
    ).scalar_one()
    for i in range(10):
        sleep(i)
        logging.info(f"Sleeping for {i} seconds")
        carina_db_session.refresh(reward_config)
        logging.info(f"Reward config status is {reward_config.status}")
        if reward_config.status == status:
            break

    assert reward_config.status == status


# POLARIS CHECKS
# fmt: off
@then("the account holder is activated",
      target_fixture="account_holder")
# fmt: on
def account_holder_is_activated(polaris_db_session: "Session", retailer_config: RetailerConfig) -> AccountHolder:
    sleep(3)
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)

    for i in range(1, 18):  # 3 minute wait
        logging.info(
            f"Sleeping for 10 seconds while waiting for account activation (account holder id: {account_holder.id})..."
        )
        sleep(3)
        polaris_db_session.refresh(account_holder)
        if account_holder.status == "ACTIVE":
            break
    logging.info(
        "\n"
        f"  Account holder status : {account_holder.status}\n"
        f"  Account number: {account_holder.account_number}\n"
        f"  Account UUID: {account_holder.account_holder_uuid}"
    )
    assert account_holder.status == "ACTIVE"
    assert account_holder.account_number is not None
    assert account_holder.account_holder_uuid is not None
    assert account_holder.opt_out_token is not None

    return account_holder


@then("the account holder activation is started")
def the_account_holder_activation_is_started(polaris_db_session: "Session", retailer_config: RetailerConfig) -> None:
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)
    assert account_holder.status == "PENDING"

    logging.info(
        f"\nAccount holder status : {account_holder.status}\n"
        f"Account number: {account_holder.account_number}\n"
        f"Account UUID: {account_holder.account_holder_uuid}"
    )

    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )

    assert resp.json()["UUID"] is not None
    assert resp.json()["email"] is not None
    assert resp.json()["status"] == "pending"
    assert resp.json()["account_number"] is not None
    assert resp.json()["current_balances"] == []
    assert resp.json()["transaction_history"] == []
    assert resp.json()["rewards"] == []
    assert resp.json()["pending_rewards"] == []


# fmt: off
@then(parse("there is no balance shown for {campaign_slug} for account holder"))
# fmt: on
def send_get_request_to_accounts_check_balance_for_campaign(
    retailer_config: RetailerConfig, account_holder: AccountHolder, campaign_slug: str
) -> None:
    time.sleep(3)
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )
    for i in range(len(resp.json()["current_balances"])):
        assert resp.json()["current_balances"][i]["campaign_slug"] != campaign_slug


@then(parse("the newly enrolled account holder's {campaign_slug} balance is {amount:d}"))
def get_account_and_check_balance(
    polaris_db_session: "Session", campaign_slug: str, amount: int, retailer_config: RetailerConfig
) -> None:
    time.sleep(2)
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)
    polaris_db_session.refresh(account_holder)
    balances_by_slug = {ahcb.campaign_slug: ahcb for ahcb in account_holder.accountholdercampaignbalance_collection}
    assert balances_by_slug[campaign_slug].balance == amount


def check_returned_account_holder_campaign_balance(
    retailer_config: RetailerConfig, account_holder: AccountHolder, campaign_slug: str, expected_amount: int
) -> None:
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )
    balance_for_campaign = {balance["campaign_slug"]: balance["value"] for balance in resp.json()["current_balances"]}[
        campaign_slug
    ]
    logging.info(f"the account holder's balance is: {int(balance_for_campaign * 100)}")
    assert int(balance_for_campaign * 100) == expected_amount


# fmt: off
@then(parse("the account holder balance shown for {campaign_slug} is {expected_balance:d}"))
# fmt: on
def check_account_balance(
    polaris_db_session: "Session", retailer_config: RetailerConfig, campaign_slug: str, expected_balance: int
) -> None:
    time.sleep(3)
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)
    check_returned_account_holder_campaign_balance(retailer_config, account_holder, campaign_slug, expected_balance)


# fmt: off
@then(parse("the balance shown for each account holder for the {campaign_slug} campaign "
            "is {expected_balance:d}"))
# fmt: on
def check_balances_for_account_holders(
    retailer_config: RetailerConfig,
    account_holders: list[AccountHolder],
    expected_balance: int,
    campaign_slug: str,
) -> None:
    for account_holder in account_holders:
        check_returned_account_holder_campaign_balance(retailer_config, account_holder, campaign_slug, expected_balance)


@then(parse("no balance is shown for each account holder for the {campaign_slug} campaign"))
def check_balance_is_is_not_present(
    polaris_db_session: "Session",
    account_holders: list[AccountHolder],
    campaign_slug: str,
) -> None:
    balances = get_account_holder_balances_for_campaign(polaris_db_session, account_holders, campaign_slug)
    assert not balances


@then(parse("the account holder's {campaign_slug} balance no longer exists"))
def check_account_holder_balance_no_longer_exists(
    campaign_slug: str,
    polaris_db_session: "Session",
    account_holder: AccountHolder,
) -> None:
    for i in range(5):
        sleep(i)
        polaris_db_session.refresh(account_holder)
        balances_by_campaign_slug = {
            ahcb.campaign_slug: ahcb.balance for ahcb in account_holder.accountholdercampaignbalance_collection
        }
        if campaign_slug in balances_by_campaign_slug:
            continue
    assert campaign_slug not in balances_by_campaign_slug


@given("an account holder reward with this reward uuid does not exist")
def check_account_holder_reward_exists(available_rewards: list[Reward], polaris_db_session: "Session") -> None:
    assert (
        polaris_db_session.execute(
            select(sql.functions.count("*"))
            .select_from(AccountHolderReward)
            .where(AccountHolderReward.reward_uuid.in_([str(reward.id) for reward in available_rewards]))
        ).scalar()
        == 0
    )


# fmt: off
@then(parse("The account holder's transaction history has {expected_num_transaction:d} transactions, "
            "and the latest transaction is {transaction_amount}"))
# fmt: on
def verify_transaction_history_balance(
    expected_num_transaction: int,
    retailer_config: RetailerConfig,
    account_holder: AccountHolder,
    transaction_amount: str,
    standard_campaign: Campaign,
) -> None:
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid} transaction history: "
        f"{json.dumps(resp.json()['transaction_history'], indent=4)}"
    )

    # Sorting the transaction history in the response. using delay to make sure there is different datetime
    time.sleep(3)
    tx_history_list = resp.json()["transaction_history"]

    assert len(tx_history_list) == expected_num_transaction
    assert resp.json()["transaction_history"][0]["datetime"] is not None
    assert resp.json()["transaction_history"][0]["amount"] == transaction_amount
    assert resp.json()["transaction_history"][0]["amount_currency"] == "GBP"
    assert resp.json()["transaction_history"][0]["location"] == "N/A"
    assert resp.json()["transaction_history"][0]["loyalty_earned_type"] == standard_campaign.loyalty_type

    if standard_campaign.loyalty_type == "ACCUMULATOR":
        assert resp.json()["transaction_history"][0]["loyalty_earned_value"] == transaction_amount

    elif standard_campaign.loyalty_type == "STAMPS":
        if transaction_amount.startswith("-"):
            assert resp.json()["transaction_history"][0]["loyalty_earned_value"] == "0"
        else:
            assert resp.json()["transaction_history"][0]["loyalty_earned_value"] == "1"


# fmt: off
@then(parse("there is {expected_num_transaction:d} transaction history in array"))
# fmt: on
def verify_transaction_history_in_get_by_credential(
    expected_num_transaction: int, retailer_config: RetailerConfig, account_holder: AccountHolder
) -> None:
    request_body = {"email": account_holder.email, "account_number": account_holder.account_number}
    resp = send_get_accounts_by_credential(retailer_config.slug, request_body)
    logging.info(f"Response for POST getbycredential HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.GETBYCREDENTIALS} transaction history: "
        f"{json.dumps(resp.json()['transaction_history'], indent=4)}"
    )
    assert resp.status_code == 200
    assert len(resp.json()["transaction_history"]) == expected_num_transaction


# fmt: off
@then(parse("BPL set up to receive only {num_of_transaction} recent transaction appeared into transaction history with "
            "{get_by_account} for the account holder"))
# fmt: on
def check_number_of_transaction_on_get_account_resonse(
    num_of_transaction: str, get_by_account: str, retailer_config: RetailerConfig, account_holder: AccountHolder
) -> None:
    if get_by_account == "get by account":
        resp = send_number_of_accounts(num_of_transaction, retailer_config.slug, account_holder.account_holder_uuid)
        logging.info(f"Response HTTP status code: {resp.status_code}")
        logging.info(
            f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
            f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
        )
    elif get_by_account == "get by credential":
        payload = {"email": account_holder.email, "account_number": account_holder.account_number}
        resp = send_number_of_accounts_by_post_credential(num_of_transaction, retailer_config.slug, payload)
        logging.info(f"Response HTTP status code: {resp.status_code}")
        logging.info(
            f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
            f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
        )
    else:
        logging.info("Couldn't find correct call services")
    assert resp.status_code == 200
    assert len(resp.json()["transaction_history"]) == int(num_of_transaction)


# fmt: off
@then(parse("{expected_num_rewards:d} {state} rewards are available to the account holder"))
# fmt: on
def check_rewards_for_account_holder(
    retailer_config: RetailerConfig,
    account_holder: AccountHolder,
    expected_num_rewards: int,
    state: str,
) -> None:
    time.sleep(10)
    resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    logging.info(f"Response HTTP status code: {resp.status_code}")
    logging.info(
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(resp.json(), indent=4)}"
    )
    if state == "issued":
        assert len(resp.json()["rewards"]) == expected_num_rewards
        for i in range(expected_num_rewards):
            assert resp.json()["rewards"][i]["code"]
            assert resp.json()["rewards"][i]["issued_date"]
            assert resp.json()["rewards"][i]["redeemed_date"] is None
            assert resp.json()["rewards"][i]["expiry_date"]
            assert resp.json()["rewards"][i]["status"] == state
    elif state == "pending":
        for i in range(expected_num_rewards):
            assert resp.json()["pending_rewards"][i]["created_date"] is not None
            assert resp.json()["pending_rewards"][i]["conversion_date"] is not None


# fmt: off
@then(parse("{expected_num_rewards:d} {state} rewards are available to each account holder"))
# fmt: on
def check_rewards_for_each_account_holder(
    retailer_config: RetailerConfig,
    account_holders: list[AccountHolder],
    expected_num_rewards: int,
    state: str,
) -> None:
    for account_holder in account_holders:
        check_rewards_for_account_holder(retailer_config, account_holder, expected_num_rewards, state)


@then(parse("any pending rewards for {campaign_slug} are deleted"))
def check_for_pending_rewards(
    polaris_db_session: "Session",
    account_holder: AccountHolder,
    campaign_slug: str,
) -> None:
    for i in range(5):
        sleep(i)
        pending_rewards = get_pending_rewards(
            polaris_db_session=polaris_db_session, account_holder=account_holder, campaign_slug=campaign_slug
        )
        if pending_rewards == []:
            break
    assert pending_rewards == []


def _get_reward_slug_from_account_holder_reward_collection(
    account_holder: AccountHolder,
    reward_slug: str,
) -> list:
    return [x for x in account_holder.accountholderreward_collection if x.reward_slug == reward_slug]


@then(parse("the {retailer_slug} account is {issued} reward {reward_slug}"))
def check_reward_issuance(
    reward_slug: str,
    issued: str,
    account_holder: AccountHolder,
    polaris_db_session: "Session",
) -> None:
    if issued == "not issued":
        for i in range(5):
            sleep(i)
            polaris_db_session.refresh(account_holder)
            account_holder_reward = _get_reward_slug_from_account_holder_reward_collection(account_holder, reward_slug)
            if not account_holder_reward:
                break
        assert not account_holder_reward
    elif issued == "issued":
        for i in range(5):
            sleep(i)
            polaris_db_session.refresh(account_holder)
            account_holder_reward = _get_reward_slug_from_account_holder_reward_collection(account_holder, reward_slug)
            if account_holder_reward:
                break
        assert account_holder_reward
    else:
        raise ValueError(f"{issued} is not an acceptable value")


@then(parse("the status of the allocated account holder for {retailer_slug} rewards are updated with {reward_status}"))
def check_account_holder_reward_statuses(
    polaris_db_session: "Session", available_rewards: list[Reward], retailer_slug: str, reward_status: str
) -> None:
    allocated_reward_codes = [reward.code for reward in available_rewards if reward.allocated]
    account_holder_rewards = (
        polaris_db_session.execute(
            select(AccountHolderReward).where(
                AccountHolderReward.code.in_(allocated_reward_codes),
                AccountHolderReward.retailer_slug == retailer_slug,
            )
        )
        .scalars()
        .all()
    )

    assert len(allocated_reward_codes) == len(account_holder_rewards)

    for account_holder_reward in account_holder_rewards:
        for i in range(6):
            time.sleep(10)  # Give it up to 1 min for the worker to do its job
            polaris_db_session.refresh(account_holder_reward)
            if account_holder_reward.status != "ISSUED":
                break

        assert account_holder_reward.status == reward_status


@then(parse("any {retailer_slug} account holder rewards for {reward_slug} are cancelled"))
def check_account_holder_rewards_are_cancelled(
    reward_slug: str,
    retailer_slug: str,
    polaris_db_session: "Session",
) -> None:
    account_holder_rewards = get_account_holder_reward(
        polaris_db_session=polaris_db_session, reward_slug=reward_slug, retailer_slug=retailer_slug
    )
    for reward in account_holder_rewards:
        if str(reward.status) == "CANCELLED":
            continue
        assert str(reward.status) == "CANCELLED"


@then(
    parse(
        "the account holder's {pending_reward_order} pending reward for {campaign_slug} has count of {count:d}, "
        "value of {value:d} and total cost to user of {total_cost_to_user:d} "
        "with conversation date {num_days:d} day in future"
    )
)
def account_holder_has_pending_reward_with_trc(
    polaris_db_session: "Session",
    account_holder: AccountHolder,
    pending_reward_order: str,
    campaign_slug: str,
    count: int,
    total_cost_to_user: int,
    value: int,
    num_days: int,
) -> None:
    time.sleep(3)

    pending_reward = get_pending_reward_by_order(
        polaris_db_session, account_holder, campaign_slug, pending_reward_order
    )

    assert pending_reward
    assert pending_reward.count == count
    assert pending_reward.total_cost_to_user == total_cost_to_user
    assert pending_reward.value == value
    assert pending_reward.conversion_date.date() == (datetime.now(tz=timezone.utc) + timedelta(days=num_days)).date()
    logging.info(
        f"\nThe latest pending reward conversion date is : {str(pending_reward.conversion_date.date())} "
        f"\nThe latest pending reward count is : {pending_reward.count} "
        f"\nThe latest pending reward value is : {pending_reward.value} "
        f"\nThe latest pending reward total cost to user is : {pending_reward.total_cost_to_user}"
    )


# fmt: off
@when(parse("the account has a pending rewards with count of {prr_count:d}, value {value:d}, "
            "total cost to user {total_cost_to_user:d} for {campaign_slug} campaign and {reward_slug} "
            "reward slug with conversation date {conversion_day:d} day in future"))
# fmt: on
def update_existing_account_holder_with_pending_rewards(
    account_holder: AccountHolder,
    retailer_config: RetailerConfig,
    prr_count: int,
    value: int,
    total_cost_to_user: int,
    polaris_db_session: "Session",
    campaign_slug: str,
    reward_slug: str,
    conversion_day: int,
) -> AccountHolderPendingReward:

    pending_rewards = create_pending_rewards_with_all_value_for_existing_account_holder(
        polaris_db_session,
        retailer_config.slug,
        conversion_day,
        prr_count,
        value,
        total_cost_to_user,
        account_holder.id,
        campaign_slug,
        reward_slug,
    )
    return pending_rewards


# VELA CHECKS
@then(parse("BPL responds with a HTTP {status_code:d} and {response_type} message"))
def the_account_holder_get_response(status_code: int, response_type: str, request_context: dict) -> None:
    assert request_context["resp"].status_code == status_code
    assert request_context["resp"].json() == TransactionResponses.get_json(response_type)
    logging.info(TransactionResponses.get_json(response_type))


# fmt: off
@when(parse("the retailer's {campaign_slug} campaign status is changed to ended with pending rewards to be "
            "{issued_or_deleted}"))
# fmt: on
def cancel_end_campaign(
    request_context: dict,
    vela_db_session: "Session",
    retailer_config: RetailerConfig,
    campaign_slug: str,
    issued_or_deleted: Literal["deleted"] | Literal["issued"],
) -> None:
    payload: dict[str, Any] = {
        "requested_status": "ended",
        "campaign_slugs": [campaign_slug],
    }
    if issued_or_deleted == "issued":
        payload.update({"issue_pending_rewards": True})
    else:
        payload.update({"issue_pending_rewards": False})

    request = send_post_campaign_status_change(
        request_context=request_context, retailer_slug=retailer_config.slug, request_body=payload
    )
    assert request.status_code == 200
    for _ in range(5):
        logging.info("Waiting for campaign status to change")
        campaign_status = get_campaign_status(vela_db_session=vela_db_session, campaign_slug=campaign_slug)
        if not campaign_status == CampaignStatuses.ENDED:
            continue
    assert campaign_status == CampaignStatuses.ENDED


# RETRY TASK CHECKS
@then(parse("a {retry_task} retryable error is received {number_of_time:d} time with {status_code:d} responses"))
def retry_task_error_received(
    polaris_db_session: "Session", retry_task: str, number_of_time: int, status_code: int
) -> None:

    for i in range(15):
        sleep(i)
        task = get_latest_task(polaris_db_session, task_name=retry_task)
        if task.audit_data is not None:
            break

    for i, data in enumerate(task.audit_data):
        if i < number_of_time:
            assert data["response"]["status"] == 500
        elif i == number_of_time:
            assert data["response"]["status"] == 200


@then("an enrolment callback task is saved in the database")
def verify_callback_task_saved_in_db(polaris_db_session: "Session", retailer_config: RetailerConfig) -> None:
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)
    callback_task = get_latest_callback_task_for_account_holder(polaris_db_session)
    assert callback_task is not None
    assert settings.MOCK_SERVICE_BASE_URL in callback_task.get_params()["callback_url"]
    assert callback_task.get_params()["third_party_identifier"] == "identifier"
    assert callback_task.get_params()["account_holder_id"] == account_holder.id


# fmt: off
@when(parse("the vela {task_name} task status is {task_status}"))
# fmt: on
def check_vela_retry_task_status_is_cancelled(vela_db_session: "Session", task_name: str, task_status: str) -> None:
    task = get_latest_task(vela_db_session, task_name)
    for i in range(5):
        sleep(i)
        if task.status.value == task_status:
            logging.info(f"{task.status} is {task_status}")
            break
        vela_db_session.refresh(task)
    assert task.status.value == task_status


# fmt: off
@then(parse("the polaris {task_name} task status is {task_status}"))
# fmt: on
def check_polaris_retry_task_status_is_success(polaris_db_session: "Session", task_name: str, task_status: str) -> None:
    task = get_latest_task(polaris_db_session, task_name)
    for i in range(10):
        sleep(i)
        if task.status.value == task_status:
            logging.info(f"{task.status} is {task_status}")
            break
        polaris_db_session.refresh(task)
    assert task.status.value == task_status


@then(parse("the {task_name} is retried {num_retried:d} time and successful on attempt {num_success:d}"))
def number_of_callback_attempts(
    polaris_db_session: "Session", task_name: str, num_retried: int, num_success: int
) -> None:
    for i in range(5):
        sleep(i)
        task = get_latest_task(polaris_db_session, task_name)
        if task.attempts == num_success:
            break
    logging.info(f"{task_name} retried number of {num_retried} time ")
    assert task.attempts == num_success


# fmt: off
@when(parse("the carina {task_name} task status is {retry_status}"))
@then(parse("the carina {task_name} task status is {retry_status}"))
# fmt: on
def check_retry_task_status_fail(carina_db_session: "Session", task_name: str, retry_status: str) -> None:

    enum_status = RetryTaskStatuses(retry_status)

    for i in range(20):
        sleep(i)
        status = get_latest_task(carina_db_session, task_name)
        if status is not None and status.status == enum_status:
            break

    assert status.status == enum_status


@then(parse("the {retry_task} did not find rewards and return {status_code:d}"))
def retry_task_not_found_rewards(carina_db_session: "Session", retry_task: str, status_code: int) -> None:

    for i in range(15):
        sleep(i)
        audit_data = get_retry_task_audit_data(carina_db_session, task_name=retry_task)
        if audit_data is not None:
            break

    logging.info(f"{retry_task} returned : {audit_data[0][0]['response']['status']} ")
    assert audit_data[0][0]["response"]["status"] == status_code


# fmt: off
@then(parse("queued reward-adjustment tasks for the account holders for the {campaign_slug} campaign are in status "
            "of {status}"))
# fmt: on
def check_reward_adjustment_tasks_for_campaign_change_status(
    account_holders: list[AccountHolder], vela_db_session: "Session", campaign_slug: str, status: str
) -> None:
    adjustment_tasks = get_tasks_by_type_and_key_value(
        vela_db_session, "reward-adjustment", "campaign_slug", campaign_slug
    )
    account_holder_uuids = [ah.account_holder_uuid for ah in account_holders]
    tasks_belonging_to_account_holders = [
        task for task in adjustment_tasks if task.get_params()["account_holder_uuid"] in account_holder_uuids
    ]
    for i in range(10):
        logging.info(f"Waiting {i} secs for reward-adjustment tasks to move to {status}")
        sleep(i)
        task_statuses = [task.status == RetryTaskStatuses[status] for task in tasks_belonging_to_account_holders]
        done = all(task_statuses)
        if done:
            break
        for task in tasks_belonging_to_account_holders:
            vela_db_session.refresh(task)
    assert done


# fmt: off
@then(parse("queued reward-issuance tasks for the account holders for the {reward_slug} reward are in status "
            "of {status}"))
# fmt: on
def check_reward_issuance_tasks_for_reward_slug_change_status(
    retailer_config: RetailerConfig,
    account_holders: list[AccountHolder],
    carina_db_session: "Session",
    reward_slug: str,
    status: str,
) -> None:
    adjustment_tasks = get_tasks_by_type_and_key_value(carina_db_session, "reward-issuance", "reward_slug", reward_slug)
    account_holder_uuids = [ah.account_holder_uuid for ah in account_holders]
    account_url_template = f"{settings.POLARIS_BASE_URL}/{retailer_config.slug}/accounts/%s/rewards"
    tasks_belonging_to_account_holders = [
        task
        for task in adjustment_tasks
        if task.get_params()["account_url"] in [account_url_template % ah_uuid for ah_uuid in account_holder_uuids]
    ]
    for i in range(10):
        logging.info(f"Waiting {i} secs for reward-issuance tasks to move to {status}")
        sleep(i)
        task_statuses = [task.status == RetryTaskStatuses[status] for task in tasks_belonging_to_account_holders]
        done = all(task_statuses)
        if done:
            break
        for task in tasks_belonging_to_account_holders:
            carina_db_session.refresh(task)
    assert done
