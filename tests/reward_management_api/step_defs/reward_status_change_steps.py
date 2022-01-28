import json
import logging
import uuid

from typing import TYPE_CHECKING, Callable, Literal, Optional, Union

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from sqlalchemy.future import select

from db.carina.models import RewardConfig
from settings import CARINA_API_AUTH_TOKEN, CARINA_BASE_URL
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response
    from sqlalchemy.orm import Session

default_headers = {
    "Authorization": f"Token {CARINA_API_AUTH_TOKEN}",
}


def send_patch_reward_type_status(
    retailer_slug: str, reward_slug: str, request_body: dict, headers: Optional[dict] = None
) -> "Response":
    logging.info(
        f"PATCH Reward type status Valid Auth token: {default_headers}\n"
        f"PATCH Reward type status  Endpoint URL:"
        f"{CARINA_BASE_URL}/{retailer_slug}/rewards/{reward_slug}/status\n"
        f"PATCH Reward type status request body: {json.dumps(request_body, indent=4)}\n"
    )
    if headers is not None and headers["token_status"] == "invalid":
        token = None
    else:
        token = default_headers
    logging.info(f"token_status: {token}")
    return retry_session().patch(
        f"{CARINA_BASE_URL}/{retailer_slug}/rewards/{reward_slug}/status",
        json=request_body,
        headers=token,
    )


@given("there are no reward configurations for invalid-test-retailer")
def noop(request_context: dict) -> None:
    request_context["retailer_slug"] = "invalid-test-retailer"


@given(parse("there is an {status} reward configuration for {retailer_slug} with unallocated rewards"))
def create_reward_config_with_available_rewards(
    create_config_and_rewards: Callable,
    retailer_slug: str,
    status: Union[Literal["ACTIVE"], Literal["CANCELLED"], Literal["ENDED"]],
    request_context: dict,
) -> None:
    request_context["reward_slug"] = reward_slug = str(uuid.uuid4()).replace("-", "")

    reward_config, reward_uuids = create_config_and_rewards(retailer_slug, reward_slug, status)

    request_context["reward_config_id"] = reward_config.id
    request_context["retailer_slug"] = retailer_slug
    logging.info(f"Active reward slug in Reward config table:{request_context}")


# fmt: off
@when(parse("I perform a PATCH operation against the {correct_incorrect} reward slug status endpoint instructing a {new_status} status change"))  # noqa: E501
# fmt: on
def patch_status(
    new_status: str, correct_incorrect: Union[Literal["correct"], Literal["incorrect"]], request_context: dict
) -> None:
    response = send_patch_reward_type_status(
        request_context["retailer_slug"],
        (request_context["reward_slug"] if correct_incorrect == "correct" else "incorrect-reward-slug"),
        {"status": new_status},
    )
    request_context["response"] = response


# fmt: off
@when(parse("I perform a PATCH operation with {invalid} token against the {correct_incorrect} reward slug status endpoint instructing a {new_status} status change"))  # noqa: E501
# fmt: on
def patch_status_invalid_token(
    new_status: str,
    invalid: str,
    correct_incorrect: Union[Literal["correct"], Literal["incorrect"]],
    request_context: dict,
) -> None:
    response = send_patch_reward_type_status(
        request_context["retailer_slug"],
        (request_context["reward_slug"] if correct_incorrect == "correct" else "incorrect-reward-slug"),
        {"status": new_status},
        {"token_status": invalid},
    )
    request_context["response"] = response


@then(parse("the status of the reward config is {new_status}"))
def check_reward_config_status(carina_db_session: "Session", new_status: str, request_context: dict) -> None:
    reward_config_status = carina_db_session.execute(
        select(RewardConfig.status).where(RewardConfig.id == request_context["reward_config_id"])
    ).scalar()
    assert reward_config_status == new_status, f"{reward_config_status} != {new_status}"


@then(parse("I get a {response_type} status response body"))
def check_response(request_context: dict, response_type: str) -> None:
    expected_response_body = response_types[response_type]
    resp = request_context["response"]
    logging.info(f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}")
    assert resp.json() == expected_response_body


response_types = {
    "invalid_token": {"display_message": "Supplied token is invalid.", "code": "INVALID_TOKEN"},
    "invalid_retailer": {"display_message": "Requested retailer is invalid.", "code": "INVALID_RETAILER"},
    "unknown_reward_slug": {"display_message": "Reward Slug does not exist.", "code": "UNKNOWN_REWARD_SLUG"},
    "update_failed": {"display_message": "Status could not be updated as requested", "code": "STATUS_UPDATE_FAILED"},
    "failed_validation": {
        "display_message": "Submitted fields are missing or invalid.",
        "code": "FIELD_VALIDATION_ERROR",
        "fields": ["status"],
    },
}
