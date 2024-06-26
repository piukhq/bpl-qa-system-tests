import json
import logging
import time

from collections import defaultdict
from time import sleep
from typing import TYPE_CHECKING, Any, Literal

import arrow

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
from tests.db_actions.hubble import get_latest_activity_by_type
from tests.db_actions.polaris import (
    create_pending_rewards_with_all_value_for_existing_account_holder,
    get_account_holder_balances_for_campaign,
    get_account_holder_for_retailer,
    get_account_holder_reward,
    get_ordered_pending_rewards,
    get_pending_rewards,
    update_account_holder_pending_rewards_conversion_date,
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
    send_post_enrolment,
)
from tests.requests.status_change import send_post_campaign_status_change
from tests.shared_utils.response_fixtures.errors import TransactionResponses
from utils import word_pos_to_list_item

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

    container.delete_blob(blobs[0])  # type: ignore [arg-type]


@then(parse("rewards are allocated to the account holder for the {reward_slug} reward"))
def check_async_reward_allocation(carina_db_session: "Session", reward_slug: str) -> None:
    """Check that the reward in the Reward table has been marked as 'allocated' and that it has an id"""
    reward_config_id = get_reward_config_id(carina_db_session=carina_db_session, reward_slug=reward_slug)

    reward_allocation_task = get_last_created_reward_issuance_task(
        carina_db_session=carina_db_session, reward_config_id=reward_config_id
    )
    for i in range(20):
        logging.info(f"Waiting {i} seconds for reward allocation task completion...")
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


# fmt: off
@then("the account holder activation is started",
      target_fixture="account_holder")
# fmt: on
def the_account_holder_activation_is_started(
    polaris_db_session: "Session", retailer_config: RetailerConfig
) -> AccountHolder:
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)
    assert account_holder.status == "ACTIVE"

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
    assert resp.json()["status"] == "active"
    assert resp.json()["account_number"] is not None
    assert resp.json()["current_balances"] == [{"campaign_slug": "N/A", "value": 0}]
    assert resp.json()["transaction_history"] == []
    assert resp.json()["rewards"] == []
    assert resp.json()["pending_rewards"] == []

    return account_holder


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


@then(parse("the account holder's {campaign_slug} balance does not exist"))
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
@then(parse("{expected_num_rewards:d} {state} rewards are available to the "
            "account holder for the {campaign_slug} campaign"))
# fmt: on
def check_rewards_for_account_holder(
    retailer_config: RetailerConfig,
    account_holder: AccountHolder,
    expected_num_rewards: int,
    state: str,
    campaign_slug: str,
) -> None:
    time.sleep(4)
    getaccount_resp = send_get_accounts(retailer_config.slug, account_holder.account_holder_uuid)
    getbycredential_resp = send_get_accounts_by_credential(
        retailer_config.slug, {"email": account_holder.email, "account_number": account_holder.account_number}
    )
    logging.info(
        f"Response HTTP status code: {getaccount_resp.status_code}"
        f"Response of GET {settings.POLARIS_BASE_URL}{Endpoints.ACCOUNTS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(getaccount_resp.json(), indent=4)}"
    )
    logging.info(
        f"Response HTTP status code: {getbycredential_resp.status_code}"
        f"Response of POST getbycredential {settings.POLARIS_BASE_URL}{Endpoints.GETBYCREDENTIALS}"
        f"{account_holder.account_holder_uuid}: {json.dumps(getbycredential_resp.json(), indent=4)}"
    )

    for resp in [getaccount_resp, getbycredential_resp]:
        if state == "issued":
            rewards_by_campaign_slug = defaultdict(list)

            for reward in resp.json()["rewards"]:
                rewards_by_campaign_slug[reward["campaign_slug"]].append(reward)

            assert len(rewards_by_campaign_slug[campaign_slug]) == expected_num_rewards
            for reward in rewards_by_campaign_slug[campaign_slug]:
                assert reward["code"]
                assert reward["issued_date"]
                assert reward["redeemed_date"] is None
                assert reward["expiry_date"]
                assert reward["status"] == state
                assert reward["campaign_slug"] == campaign_slug
        elif state == "pending":
            pending_rewards_by_campaign_slug = defaultdict(list)

            for pending_reward in resp.json()["pending_rewards"]:
                pending_rewards_by_campaign_slug[pending_reward["campaign_slug"]].append(pending_reward)

            assert len(pending_rewards_by_campaign_slug[campaign_slug]) == expected_num_rewards
            for pending_reward in pending_rewards_by_campaign_slug[campaign_slug]:
                assert pending_reward["created_date"] is not None
                assert pending_reward["conversion_date"] is not None
                assert pending_reward["campaign_slug"] == campaign_slug


# fmt: off
@then(parse("{expected_num_rewards:d} {state} rewards are available to each account holder "
            "for the {campaign_slug} campaign"))
# fmt: on
def check_rewards_for_each_account_holder(
    retailer_config: RetailerConfig,
    account_holders: list[AccountHolder],
    expected_num_rewards: int,
    state: str,
    campaign_slug: str,
) -> None:
    for account_holder in account_holders:
        check_rewards_for_account_holder(retailer_config, account_holder, expected_num_rewards, state, campaign_slug)


@then(parse("there are {num:d} pending reward records for {campaign_slug} associated with the account holder"))
def check_for_pending_rewards(
    polaris_db_session: "Session",
    account_holder: AccountHolder,
    num: int,
    campaign_slug: str,
) -> None:
    for i in range(5):
        sleep(i)
        pending_rewards = get_pending_rewards(
            polaris_db_session=polaris_db_session, account_holder=account_holder, campaign_slug=campaign_slug
        )
        if len(pending_rewards) == num:
            break
    assert len(pending_rewards) == num


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


@then(parse("the account holder has {num:d} pending reward records for the {campaign_slug} campaign"))
def account_holder_has_num_pending_reward_records(
    polaris_db_session: "Session",
    account_holder: AccountHolder,
    campaign_slug: str,
    num: int,
) -> None:
    assert len(get_ordered_pending_rewards(polaris_db_session, account_holder, campaign_slug)) == num


# fmt: off
@then(parse("the account holder's {list_position} pending reward record for {campaign_slug} has count of "
            "{count:d}, value of {value:d} and total cost to user of {total_cost_to_user:d} with a conversion "
            "date {converting}"))
# fmt: on
def account_holder_has_pending_reward_with_trc(
    polaris_db_session: "Session",
    account_holder: AccountHolder,
    list_position: str,
    campaign_slug: str,
    count: int,
    total_cost_to_user: int,
    value: int,
    converting: str,
) -> None:
    time.sleep(3)

    try:
        pending_reward = word_pos_to_list_item(
            list_position, get_ordered_pending_rewards(polaris_db_session, account_holder, campaign_slug)
        )
    except IndexError:
        assert False, f"No '{list_position}' pending reward found."

    assert pending_reward
    assert pending_reward.count == count
    assert pending_reward.total_cost_to_user == total_cost_to_user
    assert pending_reward.value == value
    assert pending_reward.conversion_date.date() == arrow.utcnow().dehumanize(converting).date()
    logging.info(
        f"\nThe {list_position} pending reward conversion date is : {str(pending_reward.conversion_date.date())} "
        f"\nThe {list_position} pending reward count is : {pending_reward.count} "
        f"\nThe {list_position} pending reward value is : {pending_reward.value} "
        f"\nThe {list_position} pending reward total cost to user is : {pending_reward.total_cost_to_user}"
    )


# fmt: off
@when(parse("the account has a pending rewards with count of {prr_count:d}, value {value:d}, "
            "total cost to user {total_cost_to_user:d} for {campaign_slug} campaign and {reward_slug} "
            "reward slug with a conversion date {converting}"))
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
    converting: str,
) -> AccountHolderPendingReward:
    pending_rewards = create_pending_rewards_with_all_value_for_existing_account_holder(
        polaris_db_session,
        retailer_config.slug,
        arrow.utcnow().dehumanize(converting).date(),
        prr_count,
        value,
        total_cost_to_user,
        account_holder.id,
        campaign_slug,
        reward_slug,
    )
    return pending_rewards


@when(parse("the account's pending rewards conversion date is {conversion_date} for {campaign_slug} campaign"))
def convert_pending_reward_conversion_date_to_now(
    polaris_db_session: "Session",
    account_holder: AccountHolder,
    retailer_config: RetailerConfig,
    conversion_date: str,
    campaign_slug: str,
) -> AccountHolderPendingReward:
    return update_account_holder_pending_rewards_conversion_date(
        polaris_db_session,
        account_holder,
        campaign_slug,
        arrow.utcnow().dehumanize(conversion_date).date(),
    )


# VELA CHECKS
@then(parse("BPL responds with a HTTP {status_code:d} and {response_type} message"))
def the_account_holder_get_response(status_code: int, response_type: str, request_context: dict) -> None:
    assert request_context["resp"].status_code == status_code
    assert request_context["resp"].json() == TransactionResponses.get_json(response_type)
    logging.info(TransactionResponses.get_json(response_type))


# fmt: off
@when(parse("the retailer's {campaign_slug} campaign is ended with pending rewards to be {issued_or_deleted}"))
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
        "activity_metadata": {"sso_username": "qa_auto"},
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
@when(parse("the {system} {task_name} task status is {task_status}"))
@then(parse("the {system} {task_name} task status is {task_status}"))
# fmt: on
def check_retry_task_status(
    polaris_db_session: "Session",
    vela_db_session: "Session",
    carina_db_session: "Session",
    system: Literal["polaris"] | Literal["vela"] | Literal["carina"],
    task_name: str,
    task_status: str,
) -> None:
    match system:
        case "polaris":
            db_session = polaris_db_session
        case "vela":
            db_session = vela_db_session
        case "carina":
            db_session = carina_db_session
        case _:
            raise ValueError("Unrecognised application")

    for i in range(20):
        task = get_latest_task(db_session, task_name)
        if task is None:
            logging.info(f"No task found. Sleeping for {i} seconds...")
            sleep(i)
            continue
        if task.status.value == task_status:
            logging.info(f"{task.status} is {task_status}")
            break
        logging.info(f"Task status is {task.status}. Sleeping for {i} seconds...")
        sleep(i)
        db_session.refresh(task)
    assert task.status.value == task_status


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
            logging.info("Found it!")
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


# fmt: off
@then(parse("{num_of_rewards:d} reward codes available for reward slug {reward_slug} "
            "with expiry date {expired_date} in the rewards table"))
# fmt: on
def available_reward_codes_in_carina(
    num_of_rewards: int, carina_db_session: "Session", reward_slug: str, expired_date: str
) -> None:
    time.sleep(3)
    for i in range(30):
        time.sleep(i)
        reward_config_id = get_reward_config_id(carina_db_session, reward_slug)
        new_uploaded_rewards = get_rewards_by_reward_config(carina_db_session, reward_config_id, allocated=False)
        if new_uploaded_rewards is not None:
            break
    assert num_of_rewards == len(new_uploaded_rewards)
    if expired_date == "None":
        for reward in new_uploaded_rewards:
            assert reward.expiry_date is None
    else:
        for reward in new_uploaded_rewards:
            assert str(reward.expiry_date) == expired_date

        logging.info(f"Reward code = {reward.code} with expiry date is = {str(reward.expiry_date)}")

    assert all([reward.code for reward in new_uploaded_rewards]), "Rewards not available"


@then(parse("there is {activity_type} activity appeared"))
def activity_type_appeared(activity_type: str, hubble_db_session: "Session") -> None:
    for i in range(30):
        time.sleep(i)
        activity = get_latest_activity_by_type(hubble_db_session=hubble_db_session, activity_type=activity_type)

        if activity is not None:
            break
        logging.info(f"waiting {i} seconds for activity appear")

    assert activity.type == activity_type
    logging.info(f"Activity type {activity.type} occurred")


@then(parse("{activity_type} activity has result field {field_value} as {result_field}"))
def activity_data_field(activity_type: str, field_value: str, result_field: str, hubble_db_session: "Session") -> None:
    for i in range(15):
        time.sleep(i)
        activity = get_latest_activity_by_type(hubble_db_session=hubble_db_session, activity_type=activity_type)
        if activity is not None:
            break

    assert activity.data[field_value] == result_field
    logging.info(f"Activity Type {activity_type} result field: {activity.data['result']}")


@when("I enrol a same account holder again")
def enrolment_again(retailer_config: "RetailerConfig") -> None:
    request_body = {
        "credentials": _get_credentials(),
        "marketing_preferences": [{"key": "marketing_pref", "value": True}],
        "callback_url": f"{settings.MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    resp = send_post_enrolment(retailer_config.slug, request_body)
    assert resp.status_code == 202

    duplicate_resp = send_post_enrolment(retailer_config.slug, request_body)
    assert duplicate_resp.status_code == 409


def _get_credentials() -> dict:
    return {
        "email": "qa_pytest_dulpicate@bink.com",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
    }


@when(parse("I enrol an account holder without {enrolment_field} field"))
def enrolment_without_field(enrolment_field: str, retailer_config: "RetailerConfig") -> None:
    credentials = _get_credentials()
    del credentials["first_name"]
    request_body = {
        "credentials": credentials,
        "marketing_preferences": [{"key": "marketing_pref", "value": True}],
        "callback_url": f"{settings.MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("Request body for POST Enrol: " + json.dumps(request_body, indent=4))
    resp = send_post_enrolment(retailer_config.slug, request_body)
    assert resp.status_code == 422
