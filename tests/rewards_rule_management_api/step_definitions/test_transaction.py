import json
import logging
import uuid

from datetime import datetime

import requests

from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse
from sqlalchemy.orm import Session

import settings

from db.polaris.models import AccountHolder, RetailerConfig
from db.vela.models import ProcessedTransaction, Transaction
from tests.rewards_rule_management_api.api_requests.base import get_rrm_headers
from tests.rewards_rule_management_api.response_fixtures.transaction import TransactionResponses

scenarios("rewards_rule_management_api/transaction/")


@given(parse("A {status} account holder exists for {retailer_slug}"))
def setup_account_holder(status: str, retailer_slug: str, request_context: dict, polaris_db_session: Session) -> None:
    email = "automated_test@transaction.test"
    retailer = polaris_db_session.query(RetailerConfig).filter_by(slug=retailer_slug).first()
    if retailer is None:
        raise ValueError(f"a retailer with slug '{retailer_slug}' was not found in the db.")
    account_status = {"active": "ACTIVE"}.get(status, "PENDING")

    account_holder = polaris_db_session.query(AccountHolder).filter_by(email=email, retailer_id=retailer.id).first()
    if account_holder is None:
        account_holder = AccountHolder(
            email=email,
            retailer_id=retailer.id,
            status=account_status,
        )
        polaris_db_session.add(account_holder)
    else:
        account_holder.status = account_status

    polaris_db_session.commit()
    request_context["account_holder_uuid"] = str(account_holder.id)
    request_context["retailer_id"] = retailer.id


@given(parse("An account holder does not exists for {retailer_slug}"))
def setup_non_existent_account_holder(retailer_slug: str, request_context: dict, polaris_db_session: Session) -> None:
    while True:
        account_holder_uuid = uuid.uuid4()
        account_holder = (
            polaris_db_session.query(AccountHolder)
            .join(RetailerConfig)
            .filter(AccountHolder.id == account_holder_uuid, RetailerConfig.slug == retailer_slug)
            .first()
        )
        if account_holder is None:
            request_context["account_holder_uuid"] = str(account_holder_uuid)
            break


@when(
    parse(
        "I send a POST transaction request with the {payload_type} payload for a {retailer_slug} with the {token} token"
    )
)
@given(
    parse(
        "A POST transaction with the {payload_type} payload for a {retailer_slug} with the {token} "
        "token was already sent"
    )
)
def send_transaction_request(payload_type: str, retailer_slug: str, token: str, request_context: dict) -> None:
    if token != "correct":
        headers = get_rrm_headers(valid_token=False)
    else:
        headers = get_rrm_headers()

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

    else:
        raise ValueError(f"{payload_type} is not a supported payload type.")

    resp = requests.post(
        f"{settings.VELA_BASE_URL}/{retailer_slug}/transaction",
        json=payload,
        headers=headers,
    )
    logging.info(
        f"Post transaction headers: {headers}\n"
        f"Post transaction URL:{settings.VELA_BASE_URL}/{retailer_slug}/transaction\n"
        f"Post transaction request body: {json.dumps(payload, indent=4)}\n"
        f"POST Transactions response: {json.dumps(resp.json(), indent=4)}"
    )
    request_context["resp"] = resp
    request_context["request_payload"] = payload


@then(parse("I get a HTTP {status_code:Number} rrm {payload_type} response", extra_types={"Number": int}))
def check_transaction_response_status(status_code: int, payload_type: str, request_context: dict) -> None:
    payload = TransactionResponses.get_json(payload_type)

    assert request_context["resp"].status_code == status_code
    if payload:
        assert request_context["resp"].json() == payload


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