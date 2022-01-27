import json
import logging
import uuid

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from retry_tasks_lib.enums import RetryTaskStatuses

from db.carina.models import Reward, RewardConfig
from tests.reward_management_api.api_requests.reward_allocation import (
    send_post_malformed_reward_allocation,
    send_post_reward_allocation,
)
from tests.reward_management_api.db_actions.reward import (
    get_allocated_reward,
    get_count_unallocated_rewards_by_reward_config,
    get_last_created_reward_allocation,
    get_reward_config,
    get_reward_config_with_available_rewards,
    get_reward_configs_ids_by_retailer,
)
from tests.reward_management_api.payloads.reward_allocation import (
    get_malformed_request_body,
    get_reward_allocation_payload,
)
from tests.reward_management_api.response_fixtures.reward_allocation import RewardAllocationResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

reward_allocation_responses = RewardAllocationResponses


@given(parse("there are rewards that can be allocated for the existing reward configs"))
def check_rewards(carina_db_session: "Session", request_context: dict) -> None:

    count_unallocated_rewards = get_count_unallocated_rewards_by_reward_config(
        carina_db_session=carina_db_session, reward_configs_ids=request_context["reward_configs_ids"]
    )
    logging.info(
        "checking that reward table contains at least 1 reward that can be allocated, "
        f"found: {count_unallocated_rewards}"
    )
    assert count_unallocated_rewards >= 1


@given(parse("there are at least {amount:d} reward configs for {retailer_slug}"))
def check_reward_configs(carina_db_session: "Session", amount: int, retailer_slug: str, request_context: dict) -> None:
    reward_configs_ids = get_reward_configs_ids_by_retailer(
        carina_db_session=carina_db_session, retailer_slug=retailer_slug
    )
    count_reward_configs = len(reward_configs_ids)
    logging.info(
        "checking that reward config table containers at least 1 config for retailer {retailer_slug}, "
        f"found: {count_reward_configs}"
    )
    assert count_reward_configs >= amount
    request_context["reward_configs_ids"] = reward_configs_ids


@then(parse("a Reward code will be allocated asynchronously"))
def check_async_reward_allocation(carina_db_session: "Session", request_context: dict) -> None:
    """Check that the reward in the Reward table has been marked as 'allocated' and that it has an id"""
    reward_allocation_task = get_last_created_reward_allocation(
        carina_db_session=carina_db_session, reward_config_id=request_context["reward_config"].id
    )

    assert reward_allocation_task != RetryTaskStatuses.WAITING

    reward = (
        carina_db_session.query(Reward).filter_by(reward_uuid=reward_allocation_task.get_params()["reward_uuid"]).one()
    )
    assert reward.allocated
    assert reward.id

    request_context["reward_allocation"] = reward_allocation_task
    request_context["reward_allocation_task_params"] = reward_allocation_task.get_params()


# fmt: off
@then(parse("the expiry date is calculated using the expiry window for the reward_slug from the Reward Management Config"))  # noqa: E501
# fmt: on
def check_reward_allocation_expiry_date(carina_db_session: "Session", request_context: dict) -> None:
    """Check that validity_days have been used to assign an expiry date"""
    # TODO: it may be possible to put back the check for hours ("%Y-%m-%d %H") once
    # https://hellobink.atlassian.net/browse/BPL-129 is done
    date_time_format = "%Y-%m-%d"
    now = datetime.utcnow()
    expiry_datetime: str = datetime.fromtimestamp(
        request_context["reward_allocation_task_params"]["expiry_date"], tz=timezone.utc
    ).strftime(date_time_format)
    expected_expiry: str = (now + timedelta(days=request_context["reward_config"].validity_days)).strftime(
        date_time_format
    )
    assert expiry_datetime == expected_expiry


@then(parse("a POST to /rewards will be made to update the users account with the reward allocation"))
def check_reward_created(polaris_db_session: "Session", request_context: dict) -> None:
    reward = get_allocated_reward(polaris_db_session, request_context["reward_allocation_task_params"]["reward_uuid"])
    assert reward.account_holder_id == request_context["account_holder"].id
    assert reward.reward_slug == request_context["reward_config"].reward_slug
    assert reward.issued_date is not None
    assert reward.expiry_date is not None
    assert reward.status == "ISSUED"


# fmt: off
@when(parse("I perform a POST operation against the allocation endpoint for a {retailer_slug} account holder with a {token} auth token"))  # noqa: E501
# fmt: on
def send_post_reward_allocation_request(
    carina_db_session: "Session", retailer_slug: str, token: str, request_context: dict
) -> None:
    reward_config: RewardConfig = get_reward_config_with_available_rewards(
        carina_db_session=carina_db_session, retailer_slug=retailer_slug
    )
    payload = get_reward_allocation_payload(request_context)
    if token == "valid":
        auth = True
    elif token == "invalid":
        auth = False
    else:
        raise ValueError(f"{token} is an invalid value for token")

    resp = send_post_reward_allocation(
        retailer_slug=retailer_slug, reward_slug=reward_config.reward_slug, request_body=payload, auth=auth
    )

    request_context["response"] = resp
    request_context["reward_config"] = reward_config


# fmt: off
@when(parse("I perform a POST operation against the allocation endpoint for a {retailer_slug} account holder with a malformed request"))  # noqa: E501
# fmt: on
def send_post_malformed_reward_allocation_request(
    carina_db_session: "Session", retailer_slug: str, request_context: dict
) -> None:
    payload = get_malformed_request_body()
    reward_config: RewardConfig = get_reward_config(carina_db_session=carina_db_session, retailer_slug=retailer_slug)
    resp = send_post_malformed_reward_allocation(
        retailer_slug=retailer_slug, reward_slug=reward_config.reward_slug, request_body=payload
    )

    request_context["response"] = resp
    request_context["reward_config"] = reward_config


# fmt: off
@when(parse("I allocate a specific reward type to an account for {retailer_slug} with a reward_slug that does not exist in the reward table"))  # noqa: E501
# fmt: on
def send_post_bad_reward_allocation_request(
    carina_db_session: "Session", retailer_slug: str, request_context: dict
) -> None:
    payload = get_reward_allocation_payload(request_context)
    reward_slug = str(uuid.uuid4())
    resp = send_post_reward_allocation(retailer_slug=retailer_slug, reward_slug=reward_slug, request_body=payload)

    request_context["response"] = resp


# fmt: off
@when(parse("I perform a POST operation against the allocation endpoint for an account holder with a non-existent retailer"))  # noqa: E501
# fmt: on
def send_post_reward_allocation_request_no_retailer(carina_db_session: "Session", request_context: dict) -> None:
    payload = get_reward_allocation_payload(request_context)

    resp = send_post_reward_allocation(
        retailer_slug="non-existent-retailer-slug", reward_slug="mock-reward-slug", request_body=payload
    )

    request_context["response"] = resp


@then(parse("I get a {response_fixture} reward allocation response body"))
def check_reward_allocation_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = reward_allocation_responses.get_json(response_fixture)
    resp = request_context["response"]
    logging.info(
        f"POST enrol expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST enrol actual response: {json.dumps(resp.json(), indent=4)}"
    )
    assert resp.json() == expected_response_body
