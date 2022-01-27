import logging
import time
import uuid

from datetime import datetime, timedelta
from pprint import pformat
from typing import TYPE_CHECKING, List

import requests

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from sqlalchemy import select

import settings

from db.carina.models import Rewards, RewardConfig
from db.polaris.models import AccountHolderReward
from tests.rewards_rule_management_api.api_requests.base import post_transaction_request
from tests.rewards_rule_management_api.db_actions.campaigns import get_active_campaigns, get_retailer_rewards

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# fmt: off
@given(parse("{retailer_slug} has an active campaign with the slug {campaign_slug} where the earn increment {earn_inc_is_tx_value} the transaction value"))  # noqa: E501
# fmt: on
def check_retailer_campaign(
    vela_db_session: "Session",
    request_context: dict,
    retailer_slug: str,
    campaign_slug: str,
    earn_inc_is_tx_value: bool,
) -> None:
    if earn_inc_is_tx_value == "is":
        earn_inc_is_tx_value = True
    elif earn_inc_is_tx_value == "is not":
        earn_inc_is_tx_value = False
    else:
        raise ValueError('earn_inc_is_tx_value must be either "is" or "is not"')
    retailer = get_retailer_rewards(vela_db_session, retailer_slug)
    assert retailer
    campaign = get_active_campaigns(
        vela_db_session,
        retailer_slug=retailer.slug,
        slug=campaign_slug,
        earn_inc_is_tx_value=earn_inc_is_tx_value,
    )[0]
    assert campaign is not None
    request_context["campaign"] = campaign


# fmt: off
@given(parse("the campaign has an earn rule threshold and a reward goal with the same value for a reward slug of {reward_slug}"))  # noqa: E501
# fmt: on
def check_earn_reward_goal(vela_db_session: "Session", reward_slug: str, request_context: dict) -> None:
    assert len(request_context["campaign"].earn_rule_collection) == 1
    earn_rule = request_context["campaign"].earn_rule_collection[0]
    assert len(request_context["campaign"].reward_rule_collection) == 1
    reward_rule = request_context["campaign"].reward_rule_collection[0]
    assert reward_rule.reward_slug == reward_slug
    assert earn_rule.threshold > reward_rule.reward_goal
    request_context["awardable_transaction_value"] = earn_rule.threshold
    request_context["reward_slug"] = reward_slug


@given(parse("there are unallocated rewards for the campaign for a reward slug of {reward_slug}"))
def check_or_make_unallocated_rewards(
    carina_db_session: "Session", polaris_db_session: "Session", reward_slug: str, request_context: dict
) -> None:
    retailer_slug = request_context["retailer_slug"]
    reward_config = (
        carina_db_session.execute(
            select(RewardConfig)
            .where(RewardConfig.retailer_slug == retailer_slug)
            .where(RewardConfig.reward_slug == reward_slug)
        )
        .scalars()
        .one()
    )
    existing_rewards = (
        carina_db_session.execute(
            select(Rewards)
            .join(RewardConfig)
            .where(Rewards.retailer_slug == retailer_slug)
            .where(Rewards.reward_config == reward_config)
            .where(Rewards.allocated.is_(False))
        )
        .scalars()
        .all()
    )
    unallocated_reward_codes = [reward.code for reward in existing_rewards]
    if len(existing_rewards) < 5:  # Let's keep enough (5?) spare rewards knocking about to mitigate against concurrency
        new_rewards = make_spare_rewards(carina_db_session, 5 - len(existing_rewards), retailer_slug, reward_config)
        unallocated_reward_codes += [reward.code for reward in new_rewards]

    request_context["unallocated_reward_codes"] = unallocated_reward_codes
    request_context["reward_config_validity_days"] = reward_config.validity_days

    # Double check these reward codes have not been added to the AccountHolderReward table
    assert (
        len(
            polaris_db_session.execute(
                select(AccountHolderReward).where(
                    AccountHolderReward.code.in_(unallocated_reward_codes),
                    AccountHolderReward.retailer_slug == retailer_slug,
                )
            )
            .scalars()
            .all()
        )
        == 0
    )


def make_spare_rewards(
    carina_db_session: "Session", how_many: int, retailer_slug: str, reward_config: RewardConfig
) -> List[Rewards]:
    rewards = []
    for _ in range(how_many):
        rewards.append(
            Rewards(
                id=str(uuid.uuid4()),
                code=str(uuid.uuid4()),
                reward_config_id=reward_config.id,
                allocated=False,
                deleted=False,
                retailer_slug=retailer_slug,
            )
        )
    carina_db_session.bulk_save_objects(rewards)
    carina_db_session.commit()
    return rewards


@when("I send a POST transaction request with a transaction value matching the reward goal for the campaign")
def send_transaction_request(request_context: dict) -> None:
    payload = {
        "id": str(uuid.uuid4()),
        "datetime": int(datetime.utcnow().timestamp()),
        "MID": "12432432",
        "loyalty_id": str(request_context["account_holder_uuid"]),
        "transaction_total": request_context["awardable_transaction_value"],
    }
    post_transaction_request(payload, request_context["retailer_slug"], "correct", request_context)


@then("A reward is allocated to the account holder")
def check_reward_allocated(polaris_db_session: "Session", request_context: dict) -> None:
    logging.info(f"Request context:\n{pformat(request_context)}")
    for i in range(5):
        time.sleep(i)
        allocated_rewards = (
            polaris_db_session.query(AccountHolderReward)
            # FIXME: BPL-190 will add a unique constraint across code and retailer at which point this query
            # should probably be updated to filter by retailer too to ensure the correct reward is retrieved
            .filter(
                AccountHolderReward.code.in_(request_context["unallocated_reward_codes"]),
                AccountHolderReward.account_holder_id == request_context["account_holder"].id,
                AccountHolderReward.reward_slug == request_context["reward_slug"],
            ).all()
        )
        if len(allocated_rewards) == 0:
            continue
        else:
            break
    assert len(allocated_rewards) == 1
    request_context["allocated_reward"] = allocated_rewards[0]


@then("the reward expiry date is the correct number of days after the issued date")
def check_reward_expiry(request_context: dict) -> None:
    reward = request_context["allocated_reward"]
    assert reward.issued_date.date() == datetime.today().date()
    assert reward.expiry_date - reward.issued_date == timedelta(days=request_context["reward_config_validity_days"])


@then("The account holder balance is updated")
def check_account_holder_balance(request_context: dict) -> None:
    earn_rule = request_context["campaign"].earn_rule_collection[0]
    reward_rule = request_context["campaign"].reward_rule_collection[0]
    retailer_slug = request_context["retailer_slug"]
    account_holder_uuid = request_context["account_holder_uuid"]
    url = f"{settings.POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_uuid}"
    headers = {
        "Authorization": f"token {settings.POLARIS_API_AUTH_TOKEN}",
        "bpl-user-channel": "automated-tests",
    }

    expected_balance = 0 + (earn_rule.increment * earn_rule.increment_multiplier) - reward_rule.reward_goal
    new_balance = 0

    def _get_balance(campaign_slug: str, account_holder_data: dict) -> int:
        return next(
            (
                int(balance["value"] * 100)
                for balance in account_holder_data["current_balances"]
                if balance["campaign_slug"] == campaign_slug
            ),
            0,
        )

    for i in range(5):
        time.sleep(i)
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        new_balance = _get_balance(request_context["campaign"].slug, resp.json())
        if new_balance == expected_balance:
            break

    assert new_balance == expected_balance
