import logging

from pytest_bdd import given, parsers, then
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from db.polaris.models import AccountHolder, RetailerConfig
from tests.rewards_rule_management_api.response_fixtures.transaction import TransactionResponses


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

    account_holder = polaris_db_session.query(AccountHolder).filter_by(email=email, retailer_id=retailer.id).first()
    if account_holder is None:

        account_holder = AccountHolder(
            email=email,
            retailer_id=retailer.id,
            status=account_status,
            current_balances={
                campaign_slug: {
                    "value": 0,
                    "campaign_slug": campaign_slug,
                }
            },
        )
        polaris_db_session.add(account_holder)
    else:
        account_holder.status = account_status
        account_holder.current_balances[campaign_slug] = {
            "value": 0,
            "campaign_slug": campaign_slug,
        }
        flag_modified(account_holder, "current_balances")

    polaris_db_session.commit()

    request_context["account_holder_uuid"] = str(account_holder.id)
    request_context["account_holder"] = account_holder
    request_context["retailer_id"] = retailer.id
    request_context["retailer_slug"] = retailer.slug
    request_context["start_balance"] = 0

    logging.info(f"Active account holder uuid:{account_holder.id}\n" f"Retailer slug: {retailer_slug}")


@given(parsers.parse("the previous response returned a HTTP {status_code:d} status code"))
@then(parsers.parse("I receive a HTTP {status_code:d} status code response"))
def check_response_status_code(status_code: int, request_context: dict) -> None:
    resp = request_context["response"]
    logging.info(f"response HTTP status code: {resp.status_code}")
    assert resp.status_code == status_code


@then(parsers.parse("I get a HTTP {status_code:d} rrm {payload_type} response"))
def check_transaction_response_status(status_code: int, payload_type: str, request_context: dict) -> None:
    payload = TransactionResponses.get_json(payload_type)

    assert request_context["resp"].status_code == status_code
    if payload:
        assert request_context["resp"].json() == payload
