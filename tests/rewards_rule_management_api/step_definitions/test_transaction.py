import uuid
from datetime import datetime

import requests
from pytest_bdd import scenarios, when, then, given
from pytest_bdd.parsers import parse
from sqlalchemy.orm import Session

import settings
from db.polaris.models import AccountHolder
from db.vela.models import Transaction
from tests.customer_management_api.db_actions.retailer import get_retailer
from tests.rewards_rule_management_api.api_requests.base import get_rrm_headers

scenarios("rewards_rule_management_api/transaction/")


@given(parse("A {status} account holder exists for {retailer_slug}"))
def setup_account_holder(status: str, retailer_slug: str, request_context: dict, polaris_db_session: Session) -> None:
    email = "automated_test@transaction.test"
    retailer = get_retailer(polaris_db_session, retailer_slug)
    status = status.upper()

    account_holder = polaris_db_session.query(AccountHolder).filter_by(email=email, retailer_id=retailer.id).first()
    if not account_holder:
        account_holder = AccountHolder(
            id=uuid.uuid4(),
            email=email,
            retailer_id=retailer.id,
            status=status.upper(),
        )
        polaris_db_session.add(account_holder)
    else:
        account_holder.status = status

    polaris_db_session.commit()
    request_context["account_holder_uuid"] = str(account_holder.id)
    request_context["retailer_id"] = retailer.id


@given("An account holder does not exists")
def setup_non_existent_account_holder(request_context: dict, polaris_db_session: Session) -> None:
    while True:
        account_holder_uuid = uuid.uuid4()
        account_holder = (
            polaris_db_session.query(AccountHolder)
            .filter_by(id=account_holder_uuid, retailer_id=request_context["retailer_id"])
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
def send_transaction_request(payload_type: str, retailer_slug: str, token: str, request_context: dict) -> None:
    if token != "correct":
        headers = get_rrm_headers(valid_token=False)
    else:
        headers = get_rrm_headers()

    if "account_holder_uuid" in request_context:
        account_holder_uuid = request_context["account_holder_uuid"]
    else:
        account_holder_uuid = uuid.uuid4()

    payload = {
        "id": str(uuid.uuid4()),
        "transaction_total": 13.25,
        "datetime": int(datetime.utcnow().timestamp()),
        "MID": "12432432",
        "loyalty_id": str(account_holder_uuid),
    }
    resp = requests.post(
        f"{settings.VELA_BASE_URL}/bpl/rewards/{retailer_slug}/transaction",
        json=payload,
        headers=headers,
    )
    request_context["resp"] = resp
    request_context["request_payload"] = payload


@then(parse("I get a HTTP {status_code} rrm response"))
def check_transaction_response_status(status_code: int, request_context: dict) -> None:
    assert request_context["resp"].status_code == status_code


@then(parse("The transaction {expectation} saved in the database"))
def check_transaction_in_db(expectation: str, vela_db_session: Session, request_context: dict) -> None:
    transaction = (
        vela_db_session.query(Transaction).filter_by(transaction_id=request_context["request_payload"]["id"]).first()
    )

    if expectation == "is":
        assert transaction is not None
    elif expectation == "is not":
        assert transaction is None
    else:
        raise ValueError(f"{expectation} is not a valid expectation")
