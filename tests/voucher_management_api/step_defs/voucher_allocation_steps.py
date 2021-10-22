import json
import logging
import uuid

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from pytest_bdd import given, parsers, then, when
from pytest_bdd.parsers import parse

from db.carina.models import Voucher, VoucherConfig
from tests.voucher_management_api.api_requests.voucher_allocation import (
    send_post_malformed_voucher_allocation,
    send_post_voucher_allocation,
)
from tests.voucher_management_api.db_actions.voucher import (
    get_allocated_voucher,
    get_count_unallocated_vouchers,
    get_count_voucher_configs,
    get_last_created_voucher_allocation,
    get_voucher_config,
)
from tests.voucher_management_api.payloads.voucher_allocation import (
    get_malformed_request_body,
    get_voucher_allocation_payload,
)
from tests.voucher_management_api.response_fixtures.voucher_allocation import VoucherAllocationResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

voucher_allocation_responses = VoucherAllocationResponses


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
    """Check that the voucher in the Voucher table has been marked as 'allocated' and that it has an id"""
    voucher_allocation_task = get_last_created_voucher_allocation(
        carina_db_session=carina_db_session, voucher_config_id=request_context["voucher_config"].id
    )
    voucher = carina_db_session.query(Voucher).filter_by(id=voucher_allocation_task.get_params()["voucher_id"]).one()
    assert voucher.allocated
    assert voucher.id

    request_context["voucher_allocation"] = voucher_allocation_task


@then(
    parsers.parse(
        "the expiry date is calculated using the expiry window for the voucher_type_slug from "
        "the Voucher Management Config"
    )
)
def check_voucher_allocation_expiry_date(carina_db_session: "Session", request_context: dict) -> None:
    """Check that validity_days have been used to assign an expiry date"""
    voucher_allocation = request_context["voucher_allocation"]
    # TODO: it may be possible to put back the check for hours ("%Y-%m-%d %H") once
    # https://hellobink.atlassian.net/browse/BPL-129 is done
    date_time_format = "%Y-%m-%d"
    now = datetime.utcnow()
    expiry_datetime: str = datetime.fromtimestamp(voucher_allocation.expiry_date, tz=timezone.utc).strftime(
        date_time_format
    )
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


@when(
    parsers.parse(
        "I perform a POST operation against the allocation endpoint for a {retailer_slug} account holder "
        "with a {token} auth token"
    )
)
def send_post_voucher_allocation_request(
    carina_db_session: "Session", retailer_slug: str, token: str, request_context: dict
) -> None:
    voucher_config: VoucherConfig = get_voucher_config(carina_db_session=carina_db_session, retailer_slug=retailer_slug)
    payload = get_voucher_allocation_payload(request_context)
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


@when(
    parsers.parse(
        "I perform a POST operation against the allocation endpoint for a {retailer_slug} account holder "
        "with a malformed request"
    )
)
def send_post_malformed_voucher_allocation_request(
    carina_db_session: "Session", retailer_slug: str, request_context: dict
) -> None:
    payload = get_malformed_request_body()
    voucher_config: VoucherConfig = get_voucher_config(carina_db_session=carina_db_session, retailer_slug=retailer_slug)
    resp = send_post_malformed_voucher_allocation(
        retailer_slug=retailer_slug, voucher_type_slug=voucher_config.voucher_type_slug, request_body=payload
    )

    request_context["response"] = resp
    request_context["voucher_config"] = voucher_config


@when(
    parsers.parse(
        "I allocate a specific voucher type to an account for {retailer_slug} with a voucher_type_slug that does not "
        "exist in the Vouchers table"
    )
)
def send_post_bad_voucher_allocation_request(
    carina_db_session: "Session", retailer_slug: str, request_context: dict
) -> None:
    payload = get_voucher_allocation_payload(request_context)
    voucher_type_slug = str(uuid.uuid4())
    resp = send_post_voucher_allocation(
        retailer_slug=retailer_slug, voucher_type_slug=voucher_type_slug, request_body=payload
    )

    request_context["response"] = resp


@when(
    parsers.parse(
        "I perform a POST operation against the allocation endpoint for an account holder with a non-existent retailer"
    )
)
def send_post_voucher_allocation_request_no_retailer(carina_db_session: "Session", request_context: dict) -> None:
    payload = get_voucher_allocation_payload(request_context)

    resp = send_post_voucher_allocation(
        retailer_slug="non-existent-retailer-slug", voucher_type_slug="mock-voucher-type-slug", request_body=payload
    )

    request_context["response"] = resp


@then(parsers.parse("I get a {response_fixture} voucher allocation response body"))
def check_voucher_allocation_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = voucher_allocation_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        f"POST enrol expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST enrol actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body
