import uuid

from datetime import datetime
from time import sleep

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from sqlalchemy.orm import Session

from db.polaris.models import AccountHolder, RetailerConfig
from db.vela.models import Campaign, ProcessedTransaction, Transaction
from tests.rewards_rule_management_api.api_requests.base import post_transaction_request


@given(parse("An account holder does not exists for {retailer_slug}"))
def setup_non_existent_account_holder(retailer_slug: str, request_context: dict, polaris_db_session: Session) -> None:
    while True:
        account_holder_uuid = uuid.uuid4()
        account_holder = (
            polaris_db_session.query(AccountHolder)
            .join(RetailerConfig)
            .filter(AccountHolder.account_holder_uuid == account_holder_uuid, RetailerConfig.slug == retailer_slug)
            .first()
        )
        if account_holder is None:
            request_context["account_holder_uuid"] = str(account_holder_uuid)
            break


# fmt: off
@when(parse("I send a POST transaction request with the {payload_type} payload for a {retailer_slug} with the {token} token"))  # noqa: E501
@given(parse("A POST transaction with the {payload_type} payload for a {retailer_slug} with the {token} token was already sent"))  # noqa: E501
# fmt: on
def send_transaction_request(payload_type: str, retailer_slug: str, token: str, request_context: dict) -> None:
    if "account_holder_uuid" in request_context:
        account_holder_uuid = request_context["account_holder_uuid"]
    else:
        account_holder_uuid = uuid.uuid4()

    payload = request_context.get("request_payload", None)
    if payload is None:
        payload = {
            "id": str(uuid.uuid4()),
            "datetime": int(datetime.utcnow().timestamp()),
            "MID": "12432432",
            "loyalty_id": str(account_holder_uuid),
        }

    if payload_type == "over the threshold":
        payload["transaction_total"] = 1000
    elif payload_type == "under the threshold":
        payload["transaction_total"] = 1
    elif payload_type == "incorrect":
        payload["transaction_total"] = "not a float"
    elif payload_type == "too early for active campaign":
        payload["transaction_total"] = 1000
        payload["datetime"] = int(datetime.fromisoformat("2021-05-10T09:00:00.000000").timestamp())
    elif payload_type == "empty values":
        payload["id"] = ""
        payload["datetime"] = ""
        payload["MID"] = ""
        payload["loyalty_id"] = ""

    else:
        raise ValueError(f"{payload_type} is not a supported payload type.")

    post_transaction_request(payload, retailer_slug, token, request_context)


@then(parse("The transaction {expectation} saved in the {transaction_table} database table"))
def check_transaction_in_db(
    expectation: str, transaction_table: str, vela_db_session: Session, request_context: dict
) -> None:
    if transaction_table == "transaction":
        model = Transaction
    elif transaction_table == "processed_transaction":
        model = ProcessedTransaction
    else:
        raise ValueError(f"{transaction_table} is an invalid transaction_table")

    transaction = (
        vela_db_session.query(model).filter_by(transaction_id=request_context["request_payload"]["id"]).first()
    )

    if expectation == "is":
        assert transaction is not None
    elif expectation == "is not":
        assert transaction is None
    else:
        raise ValueError(f"{expectation} is not a valid expectation")


@then("The transaction's amount is enough to trigger a new reward being issued")
def expected_new_balance_is_over_reward_goal(request_context: dict, vela_db_session: Session) -> None:
    campaign = (
        vela_db_session.query(Campaign)
        .filter(
            Campaign.slug == "test-campaign-1",
            Campaign.retailer_id == request_context["retailer_id"],
        )
        .first()
    )
    reward_rule = campaign.reward_rule_collection[0]
    earn_rule = campaign.earn_rule_collection[0]
    request_context["campaign"] = campaign
    request_context["reward_rule"] = reward_rule
    request_context["earn_rule"] = earn_rule

    assert (
        request_context["start_balance"] + (earn_rule.increment * earn_rule.increment_multiplier)
        >= reward_rule.reward_goal
    )


@then(parse("The account holder's balance is updated"))
def check_account_holder_balance(request_context: dict, polaris_db_session: Session, vela_db_session: Session) -> None:
    balance = request_context["balance"]
    reward_rule = request_context["reward_rule"]
    earn_rule = request_context["earn_rule"]

    expected_balance = (
        request_context["start_balance"]
        + (earn_rule.increment * earn_rule.increment_multiplier)
        - reward_rule.reward_goal
    )

    for i in range(5):
        sleep(i)
        polaris_db_session.refresh(balance)

        if balance.balance == expected_balance:
            break

    assert balance.balance == expected_balance
