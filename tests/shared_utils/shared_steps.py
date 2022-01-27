import json
import logging

from pytest_bdd import given, parsers, then
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from db.polaris.models import AccountHolder, AccountHolderCampaignBalance, RetailerConfig
from tests.rewards_rule_management_api.response_fixtures.transaction import TransactionResponses


def _setup_balance_for_account_holder(
    polaris_db_session: Session, account_holder: AccountHolder, campaign_slug: str
) -> AccountHolderCampaignBalance:
    balance = (
        polaris_db_session.execute(
            select(AccountHolderCampaignBalance).where(
                AccountHolderCampaignBalance.account_holder_id == account_holder.id,
                AccountHolderCampaignBalance.campaign_slug == campaign_slug,
            )
        )
        .scalars()
        .first()
    )

    if balance is None:
        balance = AccountHolderCampaignBalance(
            account_holder_id=account_holder.id, campaign_slug=campaign_slug, balance=0
        )
        polaris_db_session.add(balance)
    else:
        balance.balance = 0

    return balance


@given(parsers.parse("A {status} account holder exists for {retailer_slug}"))
def setup_account_holder(status: str, retailer_slug: str, request_context: dict, polaris_db_session: "Session") -> None:
    email = "user@automated.tests"
    retailer = polaris_db_session.query(RetailerConfig).filter_by(slug=retailer_slug).first()
    if retailer is None:
        raise ValueError(f"a retailer with slug '{retailer_slug}' was not found in the db.")

    account_status = {"active": "ACTIVE"}.get(status, "PENDING")
    if "campaign" in request_context:
        campaign_slug = request_context["campaign"].slug
    else:
        campaign_slug = "test-campaign-1"

    account_holder = (
        polaris_db_session.execute(
            select(AccountHolder).where(AccountHolder.email == email, AccountHolder.retailer_id == retailer.id)
        )
        .scalars()
        .first()
    )
    if account_holder is None:

        account_holder = AccountHolder(
            email=email,
            retailer_id=retailer.id,
            status=account_status,
        )
        polaris_db_session.add(account_holder)
        polaris_db_session.flush()

    else:
        account_holder.status = account_status

    balance = _setup_balance_for_account_holder(polaris_db_session, account_holder, campaign_slug)
    polaris_db_session.commit()

    request_context["account_holder_uuid"] = str(account_holder.account_holder_uuid)
    request_context["account_holder"] = account_holder
    request_context["retailer_id"] = retailer.id
    request_context["retailer_slug"] = retailer.slug
    request_context["start_balance"] = 0
    request_context["balance"] = balance

    logging.info(f"Active account holder uuid:{account_holder.account_holder_uuid}\n" f"Retailer slug: {retailer_slug}")


@given(parsers.parse("the previous response returned a HTTP {status_code:d} status code"))
@then(parsers.parse("I receive a HTTP {status_code:d} status code response"))
def check_response_status_code(status_code: int, request_context: dict) -> None:
    resp = request_context["response"]
    logging.info(
        f"Response HTTP status code: {resp.status_code} Response status: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.status_code == status_code


@then(parsers.parse("I get a HTTP {status_code:d} rrm {payload_type} response"))
def check_transaction_response_status(status_code: int, payload_type: str, request_context: dict) -> None:
    payload = TransactionResponses.get_json(payload_type)

    assert request_context["resp"].status_code == status_code
    if payload:
        assert request_context["resp"].json() == payload
