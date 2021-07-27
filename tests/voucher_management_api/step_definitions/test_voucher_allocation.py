import logging

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from pytest_bdd import given, parsers, scenarios, then, when
from pytest_bdd.parsers import parse

from db.carina.models import Voucher, VoucherConfig
from db.polaris.models import AccountHolder, RetailerConfig
from settings import POLARIS_BASE_URL
from tests.customer_management_api.step_definitions.shared import check_response_status_code
from tests.voucher_management_api.api_requests.voucher_allocation import send_post_voucher_allocation
from tests.voucher_management_api.db_actions.voucher import (
    get_allocated_voucher,
    get_count_unallocated_vouchers,
    get_count_voucher_configs,
    get_last_created_voucher_allocation,
    get_voucher_config,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

scenarios("voucher_management_api/allocation/")


@then(parsers.parse("a SUCCESS {status_code:d} is returned by the Allocation API"))
def setup_check_allocation_response_status_code(status_code: int, request_context: dict) -> None:
    check_response_status_code(status_code, request_context, "Voucher allocation")


@given(parse("A {status} account holder exists for {retailer_slug}"))
def setup_account_holder(status: str, retailer_slug: str, request_context: dict, polaris_db_session: "Session") -> None:
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
            current_balances={},
        )
        polaris_db_session.add(account_holder)
    else:
        account_holder.status = account_status

    polaris_db_session.commit()
    request_context["account_holder_uuid"] = str(account_holder.id)
    request_context["retailer"] = retailer

    try:
        campaign_value = account_holder.current_balances["test-campaign-1"]["value"]
    except KeyError:
        campaign_value = 0

    request_context["start_balance"] = campaign_value


@given(parsers.parse("there are vouchers that can be allocated"))
def check_vouchers(carina_db_session: "Session") -> None:
    count_unallocated_vouchers = get_count_unallocated_vouchers(carina_db_session=carina_db_session)
    logging.info(
        "checking that voucher table containers at least 1 voucher that can be allocated, "
        f"found: {count_unallocated_vouchers}"
    )
    assert count_unallocated_vouchers >= 1


@given(parse("there are at least {amount:d} voucher configs for {retailer_slug}"))
def check_voucher_configs(carina_db_session: "Session", amount: int, retailer_slug: str) -> None:
    count_voucher_configs = get_count_voucher_configs(carina_db_session=carina_db_session, retailer_slug=retailer_slug)
    logging.info(
        "checking that voucher config table containers at least 1 config for retailer {retailer_slug}, "
        f"found: {count_voucher_configs}"
    )
    assert count_voucher_configs >= amount


@then(parsers.parse("a Voucher code will be allocated asynchronously"))
def check_async_voucher_allocation(carina_db_session: "Session", request_context: dict) -> None:
    voucher_allocation = get_last_created_voucher_allocation(
        carina_db_session=carina_db_session, voucher_config_id=request_context["voucher_config"].id
    )
    # Check that the voucher in the Voucher table has been marked as 'allocated'
    voucher = carina_db_session.query(Voucher).filter_by(id=voucher_allocation.voucher_id).one()
    assert voucher.allocated
    assert voucher.id

    request_context["voucher_allocation"] = voucher_allocation


@then(
    parsers.parse(
        "the expiry date is calculated using the expiry window for the voucher_type_slug from "
        "the Voucher Management Config"
    )
)
def check_voucher_allocation_expiry_date(carina_db_session: "Session", request_context: dict) -> None:
    """Check that validity_days have been used to assign an expiry date"""
    voucher_allocation = request_context["voucher_allocation"]
    date_time_format = "%Y-%m-%d %H"
    now = datetime.utcnow()
    expiry_datetime: str = datetime.fromtimestamp(voucher_allocation.expiry_date).strftime(date_time_format)
    expected_expiry: str = (now + timedelta(days=request_context["voucher_config"].validity_days)).strftime(
        date_time_format
    )
    assert expiry_datetime == expected_expiry


@then(parsers.parse("a POST to /vouchers will be made to update the users account with the voucher allocation"))
def check_voucher_created(polaris_db_session: "Session", request_context: dict) -> None:
    voucher = get_allocated_voucher(polaris_db_session, request_context["voucher_allocation"].voucher_id)
    assert voucher.account_holder_id == request_context["account_holder_uuid"]
    assert voucher.voucher_type_slug == request_context["voucher_config"].voucher_type_slug
    assert voucher.issued_date is not None
    assert voucher.expiry_date is not None
    assert voucher.status == "ISSUED"


def _get_voucher_allocation_payload(request_context: dict) -> dict:
    account_holder_uuid = request_context["account_holder_uuid"]
    retailer_slug = request_context["retailer"].slug
    account_url = f"{POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_uuid}/vouchers"
    payload = {
        "account_url": account_url,
    }

    return payload


@when(
    parsers.parse(
        "I perform a POST operation against the allocation endpoint for a {retailer_slug} account holder "
        "with a {token} auth token"
    )
)
def send_valid_voucher_type_slug_request(
    carina_db_session: "Session", retailer_slug: str, token: str, request_context: dict
) -> None:
    voucher_config: VoucherConfig = get_voucher_config(carina_db_session=carina_db_session, retailer_slug=retailer_slug)
    payload = _get_voucher_allocation_payload(request_context)
    if token == "valid":
        auth = True
    elif token == "invalid":
        auth = False
    else:
        raise ValueError(f"{token} is an invalid value for token")

    resp = send_post_voucher_allocation(
        retailer_slug=retailer_slug, voucher_type_slug=voucher_config.voucher_type_slug, request_body=payload, auth=auth
    )

    request_context["response"] = resp
    request_context["voucher_config"] = voucher_config
