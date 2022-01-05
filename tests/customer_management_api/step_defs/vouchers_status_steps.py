import json
import logging

from datetime import datetime, timedelta
from uuid import uuid4

import requests

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from sqlalchemy.orm import Session

import settings

from db.polaris.models import AccountHolderVoucher
from tests.customer_management_api.api_requests.accounts import send_get_accounts
from tests.customer_management_api.response_fixtures.vouchers_status import VoucherStatusResponses


@given(parse("The account holder has an {voucher_status} voucher"))
def setup_account_holder_voucher(voucher_status: str, request_context: dict, polaris_db_session: Session) -> None:
    if voucher_status == "issued":
        status = "ISSUED"
    elif voucher_status == "non issued":
        status = "REDEEMED"
    else:
        raise ValueError(f"{voucher_status} is not a valid voucher status.")

    issued = datetime.utcnow()
    expiry = issued + timedelta(days=10)
    account_holder_id = request_context["account_holder"].id
    voucher_code = "ATMTST123456"
    voucher = (
        polaris_db_session.query(AccountHolderVoucher)
        .filter_by(
            account_holder_id=account_holder_id,
            voucher_code=voucher_code,
            voucher_type_slug="test-voucher-type",
        )
        .first()
    )

    if voucher is None:
        voucher = AccountHolderVoucher(
            voucher_id=str(uuid4()),
            voucher_code=voucher_code,
            issued_date=issued,
            expiry_date=expiry,
            voucher_type_slug="test-voucher-type",
            account_holder_id=account_holder_id,
            status=status,
            retailer_slug="test-retailer",
            idempotency_token=str(uuid4()),
        )
        polaris_db_session.add(voucher)
    else:
        voucher.status = status
        voucher.issued_date = issued
        voucher.expiry_date = expiry

    polaris_db_session.commit()
    request_context["voucher"] = voucher
    logging.info(f"Account holder's issued voucher details:{voucher_code, voucher_status}")


@when(parse("I PATCH a voucher's status to {new_status} for a {retailer_slug} using a {token_type} auth token"))
def send_voucher_status_change(new_status: str, retailer_slug: str, token_type: str, request_context: dict) -> None:
    if token_type == "valid":
        token = settings.CUSTOMER_MANAGEMENT_API_TOKEN
    elif token_type == "invalid":
        token = "INVALID-TOKEN"
    else:
        raise ValueError(f"{token_type} is an invalid token type.")

    request_context["requested_status"] = new_status
    request = {"status": new_status, "date": datetime.utcnow().timestamp()}
    request_context["resp"] = requests.patch(
        f"{settings.POLARIS_BASE_URL}/{retailer_slug}/vouchers/{request_context['voucher'].voucher_id}/status",
        json=request,
        headers={"Authorization": f"token {token}"},
    )

    logging.info(
        f"PATCH voucher URL:{settings.POLARIS_BASE_URL}/{retailer_slug}"
        f"/vouchers/{request_context['voucher'].voucher_id}/status\n "
        f"PATCH Voucher request body: {json.dumps(request, indent=4)}"
    )


@then(parse("I receive a HTTP {status_code:d} status code in the vouchers status response"))
def check_voucher_status_response(status_code: int, request_context: dict) -> None:
    logging.info(f"PATCH voucher response status code: {request_context['resp'].status_code}")
    assert request_context["resp"].status_code == status_code


@then(parse("The account holders {expectation} have the voucher's status updated in their account"))
def check_account_holder_vouchers(expectation: str, request_context: dict) -> None:
    resp = send_get_accounts(request_context["retailer_slug"], request_context["account_holder_uuid"])
    voucher = next(
        (v for v in resp.json()["vouchers"] if v["voucher_code"] == request_context["voucher"].voucher_code), None
    )
    if expectation == "will":
        assert voucher["status"] == request_context["requested_status"]  # type: ignore
    elif expectation == "will not":
        assert voucher["status"] != request_context["requested_status"]  # type: ignore
    else:
        raise ValueError(f"{expectation} is not a valid expectation")


@given("There is no voucher to update")
def setup_non_existing_voucher(request_context: dict) -> None:
    class MockVoucher:
        voucher_id = uuid4()

    request_context["voucher"] = MockVoucher


@then(parse("I get a {response_fixture} voucher status response body"))
def check_voucher_status_response_payload(response_fixture: str, request_context: dict) -> None:
    expected_response_body = VoucherStatusResponses.get_json(response_fixture)
    resp = request_context["resp"].json()
    logging.info(
        f"POST voucher_status expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST voucher_status actual response: {json.dumps(resp, indent=4)}"
    )
    assert resp == expected_response_body
