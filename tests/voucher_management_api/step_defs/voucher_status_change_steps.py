import json
import logging
import uuid

from typing import TYPE_CHECKING, Callable, Literal, Optional, Union

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from sqlalchemy.future import select

from db.carina.models import RewardConfig
from settings import CARINA_BASE_URL, VOUCHER_MANAGEMENT_API_TOKEN
from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from requests import Response
    from sqlalchemy.orm import Session

default_headers = {
    "Authorization": f"Token {VOUCHER_MANAGEMENT_API_TOKEN}",
}


def send_patch_voucher_type_status(
    retailer_slug: str, voucher_type_slug: str, request_body: dict, headers: Optional[dict] = None
) -> "Response":
    logging.info(
        f"PATCH Voucher type status Valid Auth token: {default_headers}\n"
        f"PATCH Voucher type status  Endpoint URL:"
        f"{CARINA_BASE_URL}/{retailer_slug}/vouchers/{voucher_type_slug}/status\n"
        f"PATCH Voucher type status request body: {json.dumps(request_body, indent=4)}\n"
    )
    if headers is not None and headers["token_status"] == "invalid":
        token = None
    else:
        token = default_headers
    logging.info(f"token_status: {token}")
    return retry_session().patch(
        f"{CARINA_BASE_URL}/{retailer_slug}/vouchers/{voucher_type_slug}/status",
        json=request_body,
        headers=token,
    )


@given("there are no voucher configurations for invalid-test-retailer")
def noop(request_context: dict) -> None:
    request_context["retailer_slug"] = "invalid-test-retailer"


@given(parse("there is an {status} voucher configuration for {retailer_slug} with unallocated vouchers"))
def create_voucher_config_with_available_vouchers(
    create_config_and_vouchers: Callable,
    retailer_slug: str,
    status: Union[Literal["ACTIVE"], Literal["CANCELLED"], Literal["ENDED"]],
    request_context: dict,
) -> None:
    request_context["voucher_type_slug"] = voucher_type_slug = str(uuid.uuid4()).replace("-", "")

    voucher_config, voucher_ids = create_config_and_vouchers(retailer_slug, voucher_type_slug, status)

    request_context["voucher_config_id"] = voucher_config.id
    request_context["retailer_slug"] = retailer_slug
    logging.info(f"Active voucher type slug in Voucher config table:{request_context}")


# fmt: off
@when(parse("I perform a PATCH operation against the {correct_incorrect} voucher type status endpoint instructing a {new_status} status change"))  # noqa: E501
# fmt: on
def patch_status(
    new_status: str, correct_incorrect: Union[Literal["correct"], Literal["incorrect"]], request_context: dict
) -> None:
    response = send_patch_voucher_type_status(
        request_context["retailer_slug"],
        (request_context["voucher_type_slug"] if correct_incorrect == "correct" else "incorrect-voucher-type-slug"),
        {"status": new_status},
    )
    request_context["response"] = response


# fmt: off
@when(parse("I perform a PATCH operation with {invalid} token against the {correct_incorrect} voucher type status endpoint instructing a {new_status} status change"))  # noqa: E501
# fmt: on
def patch_status_invalid_token(
    new_status: str,
    invalid: str,
    correct_incorrect: Union[Literal["correct"], Literal["incorrect"]],
    request_context: dict,
) -> None:
    response = send_patch_voucher_type_status(
        request_context["retailer_slug"],
        (request_context["voucher_type_slug"] if correct_incorrect == "correct" else "incorrect-voucher-type-slug"),
        {"status": new_status},
        {"token_status": invalid},
    )
    request_context["response"] = response


@then(parse("the status of the voucher config is {new_status}"))
def check_voucher_config_status(carina_db_session: "Session", new_status: str, request_context: dict) -> None:
    voucher_config_status = carina_db_session.execute(
        select(RewardConfig.status).where(RewardConfig.id == request_context["voucher_config_id"])
    ).scalar()
    assert voucher_config_status == new_status, f"{voucher_config_status} != {new_status}"


@then(parse("I get a {response_type} status response body"))
def check_response(request_context: dict, response_type: str) -> None:
    expected_response_body = response_types[response_type]
    resp = request_context["response"]
    logging.info(f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}")
    assert resp.json() == expected_response_body


response_types = {
    "invalid_token": {"display_message": "Supplied token is invalid.", "code": "INVALID_TOKEN"},
    "invalid_retailer": {"display_message": "Requested retailer is invalid.", "code": "INVALID_RETAILER"},
    "unknown_voucher_type": {"display_message": "Voucher Type Slug does not exist.", "code": "UNKNOWN_VOUCHER_TYPE"},
    "update_failed": {"display_message": "Status could not be updated as requested", "code": "STATUS_UPDATE_FAILED"},
    "failed_validation": {
        "display_message": "Submitted fields are missing or invalid.",
        "code": "FIELD_VALIDATION_ERROR",
        "fields": ["status"],
    },
}
