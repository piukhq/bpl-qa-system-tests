import json
import logging

from datetime import datetime, timedelta
from uuid import uuid4

import requests

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from sqlalchemy.orm import Session

import settings

from db.polaris.models import AccountHolderReward
from tests.customer_management_api.api_requests.accounts import send_get_accounts
from tests.customer_management_api.response_fixtures.rewards_status import RewardStatusResponses


@given(parse("The account holder has an {reward_status} reward"))
def setup_account_holder_reward(reward_status: str, request_context: dict, polaris_db_session: Session) -> None:
    if reward_status == "issued":
        status = "ISSUED"
    elif reward_status == "non issued":
        status = "REDEEMED"
    else:
        raise ValueError(f"{reward_status} is not a valid reward status.")

    issued = datetime.utcnow()
    expiry = issued + timedelta(days=10)
    account_holder_id = request_context["account_holder"].id
    code = str(uuid4())
    reward = (
        polaris_db_session.query(AccountHolderReward)
        .filter_by(
            account_holder_id=account_holder_id,
            code=code,
            reward_slug="test-reward-slug",
        )
        .first()
    )

    if reward is None:
        reward = AccountHolderReward(
            reward_uuid=str(uuid4()),
            code=code,
            issued_date=issued,
            expiry_date=expiry,
            reward_slug="test-reward-slug",
            account_holder_id=account_holder_id,
            status=status,
            retailer_slug="test-retailer",
            idempotency_token=str(uuid4()),
        )
        polaris_db_session.add(reward)
    else:
        reward.status = status
        reward.issued_date = issued
        reward.expiry_date = expiry

    polaris_db_session.commit()
    request_context["reward"] = reward
    logging.info(f"Account holder's issued reward details: {code, reward_status}")


@when(parse("I PATCH a reward's status to {new_status} for a {retailer_slug} using a {token_type} auth token"))
def send_reward_status_change(new_status: str, retailer_slug: str, token_type: str, request_context: dict) -> None:
    if token_type == "valid":
        token = settings.POLARIS_API_AUTH_TOKEN
    elif token_type == "invalid":
        token = "INVALID-TOKEN"
    else:
        raise ValueError(f"{token_type} is an invalid token type.")

    request_context["requested_status"] = new_status
    request = {"status": new_status, "date": datetime.utcnow().timestamp()}
    request_context["resp"] = requests.patch(
        f"{settings.POLARIS_BASE_URL}/{retailer_slug}/rewards/{request_context['reward'].reward_uuid}/status",
        json=request,
        headers={"Authorization": f"token {token}"},
    )

    logging.info(
        f"PATCH reward URL:{settings.POLARIS_BASE_URL}/{retailer_slug}"
        f"/rewards/{request_context['reward'].reward_uuid}/status\n "
        f"PATCH Reward request body: {json.dumps(request, indent=4)}"
    )


@then(parse("I receive a HTTP {status_code:d} status code in the rewards status response"))
def check_reward_status_response(status_code: int, request_context: dict) -> None:
    logging.info(f"PATCH reward response status code: {request_context['resp'].status_code}")
    assert request_context["resp"].status_code == status_code


@then(parse("The account holders {expectation} have the reward's status updated in their account"))
def check_account_holder_rewards(expectation: str, request_context: dict) -> None:
    resp = send_get_accounts(request_context["retailer_slug"], request_context["account_holder_uuid"])
    reward = next((v for v in resp.json()["rewards"] if v["code"] == request_context["reward"].code), None)
    if expectation == "will":
        assert reward["status"] == request_context["requested_status"]  # type: ignore
    elif expectation == "will not":
        assert reward["status"] != request_context["requested_status"]  # type: ignore
    else:
        raise ValueError(f"{expectation} is not a valid expectation")


@given("There is no reward to update")
def setup_non_existing_reward(request_context: dict) -> None:
    class MockReward:
        reward_uuid = uuid4()

    request_context["reward"] = MockReward


@then(parse("I get a {response_fixture} reward status response body"))
def check_reward_status_response_payload(response_fixture: str, request_context: dict) -> None:
    expected_response_body = RewardStatusResponses.get_json(response_fixture)
    resp = request_context["resp"].json()
    logging.info(
        f"POST reward_status expected response: {json.dumps(expected_response_body, indent=4)}\n"
        f"POST reward_status actual response: {json.dumps(resp, indent=4)}"
    )
    assert resp == expected_response_body
