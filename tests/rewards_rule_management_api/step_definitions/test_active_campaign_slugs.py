import json
import logging
from typing import TYPE_CHECKING

from pytest_bdd import given, when, parsers, then, scenarios

from tests.rewards_rule_management_api.api_requests.base import send_get_rrm_request, get_rrm_headers
from tests.rewards_rule_management_api.db_actions.campaigns import get_active_campaigns, get_non_active_campaigns
from tests.rewards_rule_management_api.response_fixtures.active_campaign_slugs import ActiveCampaignSlugsResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

scenarios("rewards_rule_management_api/active_campaign_slugs/")

active_campaign_slug_responses = ActiveCampaignSlugsResponses()


@given(parsers.parse("{retailer_slug} has no campaigns"))
def check_no_active_campaigns(vela_db_session: "Session", retailer_slug: str) -> None:
    active_campaigns = len(get_active_campaigns(vela_db_session, retailer_slug))
    non_active_campaigns = len(get_non_active_campaigns(vela_db_session, retailer_slug))
    logging.info(
        f"checking retailer: {retailer_slug} has no campaigns, "
        f"found: {active_campaigns + non_active_campaigns} campaigns"
    )

    assert not active_campaigns
    assert not non_active_campaigns


@given(
    parsers.parse(
        "{retailer_slug} has at least {active_campaigns_total:d} active campaign(s) "
        "and at least {non_active_campaigns_total:d} non-active campaign(s)"
    )
)
def check_campaigns(
    vela_db_session: "Session", retailer_slug: str, active_campaigns_total: int, non_active_campaigns_total: int
) -> None:
    actual_active_campaigns_total = len(get_active_campaigns(vela_db_session, retailer_slug))
    actual_non_active_campaigns_total = len(get_non_active_campaigns(vela_db_session, retailer_slug))

    logging.info(
        f"checking retailer: {retailer_slug} has at least {active_campaigns_total} active campaigns, "
        f"found: {actual_active_campaigns_total}"
    )
    assert actual_active_campaigns_total >= active_campaigns_total
    logging.info(
        f"checking retailer: {retailer_slug} has at least {non_active_campaigns_total} non-active campaigns, "
        f"found: {actual_non_active_campaigns_total}"
    )
    assert actual_non_active_campaigns_total >= non_active_campaigns_total


@when(parsers.parse("I send a get /{retailer_slug}/active-campaign-slugs request with the {token} auth token"))
def get_active_campaign_slugs(request_context: dict, retailer_slug: str, token: str) -> None:
    if token != "correct":
        headers = get_rrm_headers(valid_token=False)
    else:
        headers = get_rrm_headers()

    resp = send_get_rrm_request(f"/{retailer_slug}/active-campaign-slugs", headers=headers)
    request_context["response"] = resp


@then(parsers.parse("I receive a HTTP {status_code:d} status code response for my GET active-campaign-slugs request"))
def check_response_status_code(status_code: int, request_context: dict) -> None:
    resp = request_context["response"]
    logging.info(f"GET active-campaign-slugs response HTTP status code: {resp.status_code}")
    assert resp.status_code == status_code


@then(
    parsers.parse(
        "I get all the active campaign slugs for {retailer_slug} " "in my GET active_campaign_slugs response body"
    )
)
def check_active_campaign_slugs_response(vela_db_session: "Session", request_context: dict, retailer_slug: str) -> None:
    active_campaigns = get_active_campaigns(vela_db_session, retailer_slug)
    expected_response_body = [campaign.slug for campaign in active_campaigns]

    resp = request_context["response"]
    logging.info(
        f"POST enrol expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST enrol actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body


@then(parsers.parse("I get a {response_fixture} GET active-campaign-slugs response body"))
def check_active_campaign_slugs_error_response(
    vela_db_session: "Session", response_fixture: str, request_context: dict
) -> None:
    expected_response_body = active_campaign_slug_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        f"POST enrol expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST enrol actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body
