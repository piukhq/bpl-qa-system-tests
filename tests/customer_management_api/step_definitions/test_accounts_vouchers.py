import random
import string
import uuid

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from pytest_bdd import given, parsers, scenarios, then, when

from db.polaris.models import AccountHolderVoucher
from tests.customer_management_api.api_requests.accounts_vouchers import send_post_accounts_voucher
from tests.customer_management_api.response_fixtures.vouchers import VoucherResponses
from tests.customer_management_api.step_definitions.shared import (
    check_account_holder_is_active,
    check_response_status_code,
    enrol_account_holder,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


scenarios("customer_management_api/accounts_vouchers/")


@given(parsers.parse("I previously successfully enrolled a {retailer_slug} account holder"))
def setup_account_holder(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context)


@given(parsers.parse("I received a HTTP {status_code:d} status code response"))
def setup_check_enrolment_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "Enrol")


@given(parsers.parse("the enrolled account holder has been activated"))
def check_account_holder_is_activated(polaris_db_session: "Session", request_context: dict) -> None:
    account_holder = check_account_holder_is_active(polaris_db_session, request_context)
    request_context["account_holder"] = account_holder


@when(parsers.parse("I POST a voucher for a {retailer_slug} account holder with a {token_validity} auth token"))
@given(parsers.parse("I POST a voucher for a {retailer_slug} account holder with a {token_validity} auth token"))
def post_voucher(polaris_db_session: "Session", retailer_slug: str, token_validity: str, request_context: dict) -> None:
    if "account_holder" in request_context:
        account_holder_id = request_context["account_holder"].id
    else:
        account_holder_id = str(uuid.uuid4())

    request_context["voucher_id"] = str(uuid.uuid4())

    payload = {
        "voucher_id": request_context["voucher_id"],
        "voucher_code": "".join(random.choice(string.ascii_lowercase) for i in range(10)),
        "voucher_type_slug": "voucher-type-slug",
        "issued_date": datetime.utcnow().timestamp(),
        "expiry_date": (datetime.utcnow() + timedelta(days=7)).timestamp(),
    }
    resp = send_post_accounts_voucher(
        retailer_slug,
        account_holder_id,
        payload,
        "valid" if token_validity == "valid" else "invalid",  # jump through mypy hoops
    )
    request_context["response"] = resp


@then(parsers.parse("I receive a HTTP {status_code:d} status code in the voucher response"))
def check_voucher_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "vouchers")


@then(parsers.parse("the account holder's voucher is created in the database"))
def check_voucher_created(polaris_db_session: "Session", status_code: int, request_context: dict) -> None:
    voucher = polaris_db_session.query(AccountHolderVoucher).filter_by(voucher_id=request_context["voucher_id"]).one()
    assert voucher.account_holder_id == str(request_context["account_holder"].id)
    assert voucher.issued_date is not None
    assert voucher.expiry_date is not None
    assert voucher.status == "ISSUED"
    assert voucher.redeemed_date is None
    assert voucher.cancelled_date is None


@then(parsers.parse("I get a {response_fixture} voucher response body"))
def check_adjustments_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = VoucherResponses.get_json(response_fixture)
    resp = request_context["response"]
    assert resp.json() == expected_response_body
