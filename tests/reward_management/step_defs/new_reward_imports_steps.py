import logging
import uuid

from time import sleep
from typing import TYPE_CHECKING, Callable, List, Optional

from pytest_bdd import given, then
from pytest_bdd.parsers import parse
from sqlalchemy.future import select

from db.carina.models import Rewards, RewardConfig

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@given(parse("{retailer_slug} has pre-existing rewards for the {reward_slug} reward slug"))
def make_pre_existing_rewards(
    retailer_slug: str,
    reward_slug: str,
    get_reward_config: Callable[[str, str], RewardConfig],
    create_mock_rewards: Callable,
    request_context: dict,
) -> None:
    pre_existing_rewards: List[Rewards] = create_mock_rewards(
        reward_config=get_reward_config(retailer_slug, reward_slug),
        n_rewards=3,
        reward_overrides=[
            {"allocated": True},
            {"allocated": False},
            {"allocated": False, "deleted": True},
        ],
    )
    request_context["pre_existing_reward_codes"] = [v.code for v in pre_existing_rewards]


@given(parse("{retailer_slug} provides a csv file in the correct format for the {reward_slug} reward slug"))
def put_new_rewards_file(
    retailer_slug: str,
    reward_slug: str,
    request_context: dict,
    upload_available_rewards_to_blob_storage: Callable,
) -> None:
    new_reward_codes = request_context["import_file_new_reward_codes"] = [str(uuid.uuid4()) for _ in range(5)]
    blob = upload_available_rewards_to_blob_storage(
        retailer_slug,
        new_reward_codes + request_context.get("pre_existing_reward_codes", []),
        reward_slug=reward_slug,
    )
    assert blob
    request_context["blob"] = blob


@then("only unseen rewards are imported by the reward management system")
def check_new_rewards_imported(request_context: dict, carina_db_session: "Session") -> None:
    new_codes = request_context["import_file_new_reward_codes"]
    pre_existing_codes = request_context["pre_existing_reward_codes"]
    rewards: Optional[List[Rewards]] = None
    for i in range(7):
        logging.info("Sleeping for 10 seconds...")
        sleep(10)
        rewards = (
            carina_db_session.execute(select(Rewards).where(Rewards.code.in_(new_codes + pre_existing_codes)))
            .scalars()
            .all()
        )
        if rewards and len(rewards) != len(new_codes + pre_existing_codes):
            logging.info("New reward codes not found...")
            continue
        else:
            break

    expected_codes = sorted(
        request_context["import_file_new_reward_codes"] + request_context["pre_existing_reward_codes"]
    )
    db_codes = sorted([r.code for r in rewards]) if rewards else None
    assert expected_codes == db_codes


@then("the reward codes are not imported")
def check_rewards_not_imported(carina_db_session: "Session", request_context: dict) -> None:
    rewards = (
        carina_db_session.execute(
            select(Rewards).where(Rewards.code.in_(request_context["import_file_new_reward_codes"]))
        )
        .scalars()
        .all()
    )
    assert not rewards
