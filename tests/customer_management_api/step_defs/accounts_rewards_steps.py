import json
import logging
import random
import string
import uuid

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse

from settings import POLARIS_BASE_URL
from tests.customer_management_api.api_requests.accounts_rewards import send_post_accounts_reward
from tests.customer_management_api.db_actions.account_holder import get_account_holder_reward
from tests.customer_management_api.response_fixtures.rewards import RewardResponses

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# fmt: off
@when(parse("I POST a reward expiring in the {past_or_future} for a {retailer_slug} account holder with a {token_validity} auth token"))  # noqa: E501
@given(parse("I POST a reward expiring in the {past_or_future} for a {retailer_slug} account holder with a {token_validity} auth token"))  # noqa: E501
# fmt: on
def post_reward(past_or_future: str, retailer_slug: str, token_validity: str, request_context: dict) -> None:
    if "account_holder" in request_context:
        account_holder_uuid = request_context["account_holder"].account_holder_uuid
    else:
        account_holder_uuid = str(uuid.uuid4())

    request_context["reward_uuid"] = str(uuid.uuid4())

    payload = {
        "reward_uuid": request_context["reward_uuid"],
        "code": "".join(random.choice(string.ascii_lowercase) for i in range(10)),
        "reward_slug": "reward-slug",
        "issued_date": datetime.utcnow().timestamp(),
        "expiry_date": (datetime.utcnow() + timedelta(days=-7 if past_or_future == "past" else 7)).timestamp(),
    }
    resp = send_post_accounts_reward(
        retailer_slug,
        account_holder_uuid,
        payload,
        "valid" if token_validity == "valid" else "invalid",  # jump through mypy hoops
    )
    logging.info(
        f"POST Reward Endpoint request body: {json.dumps(payload, indent=4)}\n"
        f"Post Reward URL:{POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_uuid}/rewards"
    )
    request_context["response"] = resp


@then(parse("I get a {response_fixture} reward response body"))
def check_reward_response(response_fixture: str, request_context: dict) -> None:
    expected_response_body = RewardResponses.get_json(response_fixture)
    resp = request_context["response"]
    assert resp.json() == expected_response_body
    logging.info(f"Response Body: {json.dumps(resp.json(), indent=4)}")


@then(parse("the returned reward's status is {status} and the reward data is well formed"))
def check_reward_status(polaris_db_session: "Session", status: str, request_context: dict) -> None:
    correct_keys = ["code", "issued_date", "redeemed_date", "expiry_date", "status"]
    reward_response = request_context["response"].json()
    reward_list = reward_response["rewards"]
    assert len(reward_list) == 1
    assert reward_list[0]["status"] == status.lower()
    assert list(reward_list[0].keys()) == correct_keys
    code = reward_list[0].get("code")
    assert bool(code) is True
    account_holder_reward = get_account_holder_reward(
        polaris_db_session, code, request_context["retailer_slug"]
    )
    assert reward_list[0]["issued_date"] == int(
        account_holder_reward.issued_date.replace(tzinfo=timezone.utc).timestamp()
    )
    assert reward_list[0]["expiry_date"] == int(
        account_holder_reward.expiry_date.replace(tzinfo=timezone.utc).timestamp()
    )
    assert reward_list[0]["redeemed_date"] is None
