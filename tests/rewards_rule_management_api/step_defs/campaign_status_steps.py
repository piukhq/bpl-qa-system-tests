import json
import logging
import uuid

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from pytest_bdd import given, parsers, then, when

from db.carina.models import VoucherConfig
from db.vela.models import Campaign, CampaignStatuses
from tests.rewards_rule_management_api.api_requests.campaign_status import (
    send_post_campaign_status_change,
    send_post_malformed_campaign_status_change,
)
from tests.rewards_rule_management_api.db_actions.campaigns import get_active_campaigns, get_non_active_campaigns
from tests.rewards_rule_management_api.payloads.campaign_status_change import (
    get_campaign_status_change_payload,
    get_malformed_request_body,
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


@given(parsers.parse("{retailer_slug} has at least {active_campaigns_total:d} active campaign(s)"))
def check_campaigns(
    vela_db_session: "Session", retailer_slug: str, active_campaigns_total: int, request_context: dict
) -> None:
    active_campaigns: list[Campaign] = get_active_campaigns(vela_db_session, retailer_slug)
    actual_active_campaigns_total = len(active_campaigns)

    logging.info(
        f"checking retailer: {retailer_slug} has at least {active_campaigns_total} active campaigns, "
        f"found: {actual_active_campaigns_total}"
    )
    assert actual_active_campaigns_total >= active_campaigns_total

    request_context["retailer_slug"] = retailer_slug
    request_context["active_campaigns"] = active_campaigns


@when(
    parsers.parse(
        "I perform a POST operation against the status change endpoint for a {status} status for "
        "a {retailer_slug} retailer "
        "with a {token} auth token"
    )
)
def send_post_campaign_change_request(
    vela_db_session: "Session", status: str, retailer_slug: str, token: str, request_context: dict
) -> None:
    request_context["active_campaigns"] = request_context["active_campaigns"][:1]  # only need the first one
    payload = get_campaign_status_change_payload(request_context)
    if token == "valid":
        auth = True
    elif token == "invalid":
        auth = False
    else:
        raise ValueError(f"{token} is an invalid value for token")

    resp = send_post_campaign_status_change(retailer_slug=retailer_slug, request_body=payload, auth=auth)

    request_context["response"] = resp


@then(parsers.parse("the campaign status should be updated in Vela"))
def check_campaign_status(vela_db_session: "Session", request_context: dict) -> None:
    campaign = request_context["active_campaigns"][0]
    vela_db_session.refresh(campaign)
    assert campaign.status == CampaignStatuses.ENDED


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
