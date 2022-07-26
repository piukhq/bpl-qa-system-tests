import json
import logging
import time

from datetime import datetime
from time import sleep
from typing import TYPE_CHECKING, Any, Callable, Literal
from uuid import uuid4

from faker import Faker
from pytest_bdd import scenarios, then, when
from pytest_bdd.parsers import parse
from retry_tasks_lib.enums import RetryTaskStatuses
from sqlalchemy import func, select

import settings

from azure_actions.blob_storage import check_archive_blobcontainer
from db.carina.models import Retailer, Reward, RewardConfig
from db.polaris.models import AccountHolder, AccountHolderCampaignBalance, AccountHolderReward, RetailerConfig
from db.vela.models import Campaign, CampaignStatuses
from settings import MOCK_SERVICE_BASE_URL
from tests.api.base import Endpoints
from tests.db_actions.carina import get_reward_config_id, get_rewards, get_rewards_by_reward_config
from tests.db_actions.polaris import get_account_holder_for_retailer, get_account_holder_reward, get_pending_rewards
from tests.db_actions.retry_tasks import (
    get_latest_callback_task_for_account_holder,
    get_latest_task,
    get_retry_task_audit_data,
    get_tasks_by_type_and_key_value,
)
from tests.db_actions.reward import get_last_created_reward_issuance_task
from tests.db_actions.vela import get_campaign_status, get_reward_adjustment_task_status
from tests.requests.enrolment import (
    send_get_accounts,
    send_get_accounts_by_credential,
    send_number_of_accounts,
    send_number_of_accounts_by_post_credential,
    send_post_enrolment,
)
from tests.requests.status_change import send_post_campaign_status_change
from tests.requests.transaction import post_transaction_request
from tests.shared_utils.response_fixtures.errors import TransactionResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

scenarios("../features/trenette")
scenarios("../features/asos")

fake = Faker(locale="en_GB")


@then("Retailer, Campaigns, and RewardConfigs are successfully created in the database")
def enrolment(
    retailer_config: RetailerConfig, standard_campaigns: list[Campaign], standard_reward_configs: list[RewardConfig]
) -> None:
    assert retailer_config is not None
    assert standard_campaigns
    assert standard_reward_configs


@when(parse("i Enrol a account holder passing in all required and all optional fields"))
@when(parse("the account holder enrol to retailer with all required and all optional fields"))
def enrol_accountholder_with_all_required_fields(retailer_config: RetailerConfig) -> None:
    return enrol_account_holder(retailer_config)


def enrol_account_holder(
    retailer_config: RetailerConfig,
    incl_optional_fields: bool = True,
    callback_url: str | None = None,
) -> None:
    if incl_optional_fields:
        request_body = all_required_and_all_optional_credentials(callback_url=callback_url)
    else:
        request_body = only_required_credentials()
    resp = send_post_enrolment(retailer_config.slug, request_body)
    time.sleep(3)
    logging.info(
        f"Response HTTP status code for enrolment: {resp.status_code} "
        f"Response status: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.status_code == 202
    logging.info(f"Account holder response: {resp}")


def all_required_and_all_optional_credentials(callback_url: str | None = None) -> dict:
    payload = {
        "credentials": _get_credentials(),
        "marketing_preferences": [{"key": "marketing_pref", "value": True}],
        "callback_url": callback_url or f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("`Request body for POST Enrol: " + json.dumps(payload, indent=4))
    return payload


def _get_credentials() -> dict:
    return {
        "email": f"qa_pytest_{uuid4()}@bink.com",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
    }


def only_required_credentials() -> dict:
    credentials = _get_credentials()
    del credentials["address_line2"]
    del credentials["postcode"]
    del credentials["city"]
    payload = {
        "credentials": credentials,
        "marketing_preferences": [{"key": "marketing_pref", "value": True}],
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("Request body for POST Enrol: " + json.dumps(payload, indent=4))
    return payload


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


@then("an enrolment callback task is saved in the database")
def verify_callback_task_saved_in_db(polaris_db_session: "Session", retailer_config: RetailerConfig) -> None:
    account_holder = get_account_holder_for_retailer(polaris_db_session, retailer_config.id)
    callback_task = get_latest_callback_task_for_account_holder(polaris_db_session)
    assert callback_task is not None
    assert settings.MOCK_SERVICE_BASE_URL in callback_task.get_params()["callback_url"]
    assert callback_task.get_params()["third_party_identifier"] == "identifier"
    assert callback_task.get_params()["account_holder_id"] == account_holder.id


@when(parse("the account holder POST transaction request for {retailer_slug} retailer with {amount:d}"))
def the_account_holder_transaction_request(retailer_slug: str, amount: int, request_context: dict) -> None:
    account_holder_uuid = request_context["account_holder_uuid"]

    payload = {
        "id": str(uuid4()),
        "transaction_total": amount,
        "datetime": int(datetime.utcnow().timestamp()),
        "MID": "12432432",
        "loyalty_id": str(account_holder_uuid),
        "transaction_id": "BPL1234567891",
    }
    logging.info(f"Payload of transaction : {json.dumps(payload)}")
    post_transaction_request(payload, retailer_slug, request_context)


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
    # status: Literal['cancelled'] | Literal['ended'],
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


# fmt: off
@then(parse("the retailer's {campaign_slug} campaign status is changed to {status}"))
# fmt: on
def send_post_campaign_change_request(
    request_context: dict,
    status: str,
    retailer_config: RetailerConfig,
    campaign_slug: str,
) -> None:
    payload: dict[str, Any] = {
        "requested_status": status,
        "campaign_slugs": [campaign_slug],
    }

    request = send_post_campaign_status_change(
        request_context=request_context, retailer_slug=retailer_config.slug, request_body=payload
    )
    assert request.status_code == 200


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


@then(parse("the reward adjustment retry task for {campaign_slug} has a status of {status}"))
def check_reward_adjustment_task_status_is_failed(
    vela_db_session: "Session",
    campaign_slug: str,
    status: str,
) -> None:
    resp = get_reward_adjustment_task_status(vela_db_session, campaign_slug)
    assert resp == status


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


# fmt: off
@when(parse("the {retailer_slug} retailer updates selected rewards to {reward_status} status"),
      target_fixture="imported_reward_ids")
# fmt: on
def reward_updates_upload(
    retailer_slug: str,
    reward_status: str,
    available_rewards: list[Reward],
    upload_reward_updates_to_blob_storage: Callable,
) -> list[str]:
    """
    The fixture should place a CSV file onto blob storage, which a running instance of
    carina (the scheduler job for doing these imports) will pick up and process, putting rows into carina's DB
    for today's date.
    """
    blob = upload_reward_updates_to_blob_storage(
        retailer_slug=retailer_slug, rewards=available_rewards, reward_status=reward_status
    )
    assert blob
    return [reward.id for reward in available_rewards]


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


@then(parse("{num_rewards:d} rewards are allocated to the account holder for the {reward_slug} reward"))
def check_async_reward_allocation(
    num_rewards: int, carina_db_session: "Session", request_context: dict, reward_slug: str
) -> None:
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


@then(parse("all unallocated rewards for {reward_slug} reward config are soft deleted"))
def check_unallocated_rewards_deleted(
    carina_db_session: "Session",
    reward_slug: str,
) -> None:
    reward_config_id = get_reward_config_id(carina_db_session, reward_slug)
    unallocated_rewards = get_rewards_by_reward_config(carina_db_session, reward_config_id, allocated=False)
    for i in range(3):
        time.sleep(i)  # Need to allow enough time for the task to soft delete rewards
        rewards_deleted = []
        for reward in unallocated_rewards:
            carina_db_session.refresh(reward)
            rewards_deleted.append(reward.deleted)

        if all(rewards_deleted):
            break

    assert all(rewards_deleted), "All rewards not soft deleted"


@then(parse("any pending rewards for {campaign_slug} are deleted"))
def check_for_pending_rewards(
    polaris_db_session: "Session",
    campaign_slug: str,
) -> None:
    for i in range(5):
        sleep(i)
        pending_rewards = get_pending_rewards(polaris_db_session=polaris_db_session, campaign_slug=campaign_slug)
        if pending_rewards == []:
            break
    assert pending_rewards == []


# fmt: off
@when(parse("an account holder is enrolled passing in all required and optional fields with a callback URL for "
            "{num_failures:d} consecutive HTTP {status_code:d} responses"))
# fmt: on
def post_enrolment_with_known_repeated_callback(
    retailer_config: RetailerConfig, num_failures: int, status_code: int
) -> None:
    enrol_account_holder(
        retailer_config, callback_url=get_callback_url(num_failures=num_failures, status_code=status_code)
    )


def get_callback_url(
    *,
    num_failures: int | None = None,
    status_code: int | None = None,
    timeout_seconds: int | None = 60,
) -> str:
    if status_code is None:
        location = f"/enrol/callback/timeout-{timeout_seconds}"
    elif status_code == 200:
        location = "/enrol/callback/success"
    elif status_code == 500 and num_failures is not None:
        location = f"/enrol/callback/retry-{num_failures}"
    else:
        location = f"/enrol/callback/error-{status_code}"
    return f"{settings.MOCK_SERVICE_BASE_URL}{location}"


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


@then(parse("the file is moved to the {container_type} container by the reward importer"))
def check_file_moved(
    container_type: Literal["archive"] | Literal["error"],
) -> None:
    blobs, container = check_archive_blobcontainer(container_type)

    assert len(blobs) == 1

    container.delete_blob(blobs[0])


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


@then(parse("the {retry_task} did not find rewards and return {status_code:d}"))
def retry_task_not_found_rewards(carina_db_session: "Session", retry_task: str, status_code: int) -> None:

    for i in range(15):
        sleep(i)
        audit_data = get_retry_task_audit_data(carina_db_session, task_name=retry_task)
        if audit_data is not None:
            break

    logging.info(f"{retry_task} returned : {audit_data[0][0]['response']['status']} ")
    assert audit_data[0][0]["response"]["status"] == status_code


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
@then(parse("there is {expected_num_transaction:d} transaction record with amount {transaction_amount} "
            "for {campaign_type} campaign"))
# fmt: on
def verify_transaction_history_balance(
    expected_num_transaction: int,
    retailer_config: RetailerConfig,
    account_holder: AccountHolder,
    transaction_amount: str,
    campaign_type: str,
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
    tx_history_sorted = sorted(tx_history_list, key=lambda d: d["datetime"])

    assert len(tx_history_list) == expected_num_transaction
    assert tx_history_sorted[expected_num_transaction - 1]["datetime"] is not None
    assert tx_history_sorted[expected_num_transaction - 1]["amount"] == transaction_amount
    assert tx_history_sorted[expected_num_transaction - 1]["amount_currency"] == "GBP"
    assert tx_history_sorted[expected_num_transaction - 1]["location"] == "N/A"
    assert tx_history_sorted[expected_num_transaction - 1]["loyalty_earned_type"] == campaign_type

    if campaign_type == "ACCUMULATOR":
        assert tx_history_sorted[expected_num_transaction - 1]["loyalty_earned_value"] == transaction_amount

    elif campaign_type == "STAMPS":
        assert tx_history_sorted[expected_num_transaction - 1]["loyalty_earned_value"] == 1


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
def set_up_number_of_transaction(
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


def get_account_holder_balances_for_campaign(
    polaris_db_session: "Session", account_holders: list[AccountHolder], campaign_slug: str
) -> list[AccountHolderCampaignBalance]:
    return (
        polaris_db_session.execute(
            select(AccountHolderCampaignBalance).where(
                AccountHolderCampaignBalance.account_holder_id.in_([ah.id for ah in account_holders]),
                AccountHolderCampaignBalance.campaign_slug == campaign_slug,
            )
        )
        .scalars()
        .all()
    )


@then(parse("no balance is shown for each account holder for the {campaign_slug} campaign"))
def check_balance_is_is_not_present(
    polaris_db_session: "Session",
    account_holders: list[AccountHolder],
    campaign_slug: str,
) -> None:
    balances = get_account_holder_balances_for_campaign(polaris_db_session, account_holders, campaign_slug)
    assert not balances
