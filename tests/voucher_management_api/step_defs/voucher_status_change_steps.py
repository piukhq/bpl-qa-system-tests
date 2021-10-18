import json
import logging
import uuid

from typing import Callable, Literal, Optional, Union, TYPE_CHECKING

from pytest_bdd import given, then, when
from pytest_bdd.parsers import parse
from sqlalchemy.future import select  # type: ignore

from db.carina.models import VoucherConfig
from settings import CARINA_BASE_URL, VOUCHER_MANAGEMENT_API_TOKEN

from tests.retry_requests import retry_session

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from requests import Response

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


@when(
    parse(
        "I perform a PATCH operation against the {correct_incorrect} voucher type status endpoint instructing a "
        "{new_status} status change"
    )
)
def patch_status(
        new_status: str, correct_incorrect: Union[Literal["correct"], Literal["incorrect"]], request_context: dict
) -> None:
    response = send_patch_voucher_type_status(
        request_context["retailer_slug"],
        (request_context["voucher_type_slug"] if correct_incorrect == "correct" else "incorrect-voucher-type-slug"),
        {"status": new_status},
    )
    request_context["response"] = response


@when(
    parse(
        "I perform a PATCH operation with {invalid} token against the {correct_incorrect} voucher type status endpoint "
        "instructing a {new_status} status change"
    )
)
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
        select(VoucherConfig.status).where(VoucherConfig.id == request_context["voucher_config_id"])
    ).scalar()
    assert voucher_config_status == new_status, f"{voucher_config_status} != {new_status}"


@then(parse("I get a {invalid_token} status response body"))
def check_invalid_token_status(request_context: dict) -> None:
    expected_response_body = {"display_message": "Supplied token is invalid.", "error": "INVALID_TOKEN"}
    resp = request_context["response"]
    logging.info(f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}")
    assert resp.json() == expected_response_body


@then(parse("i receive {invalid_retailer} response message"))
def check_invalid_retailer(request_context: dict) -> None:
    expected_response_body = {"display_message": "Requested retailer is invalid.",
                              "error": "INVALID_RETAILER"
                              }
    resp = request_context["response"]
    logging.info(f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}")
    assert resp.json() == expected_response_body


@then(parse("I receive {unknown_voucher} response body"))
def check_unknown_voucher_type(request_context: dict) -> None:
    expected_response_body = {"display_message": "Voucher Type Slug does not exist.",
                              "error": "UNKNOWN_VOUCHER_TYPE"
                              }
    resp = request_context["response"]
    logging.info(f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}")
    assert resp.json() == expected_response_body


@then(parse("I receive status {update_failed} response body"))
def check_status_update_fail(request_context: dict) -> None:
    expected_response_body = {"display_message": "Status could not be updated as requested",
                              "error": "STATUS_UPDATE_FAILED"
                              }
    resp = request_context["response"]
    logging.info(f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}")
    assert resp.json() == expected_response_body


@then(parse("I get a {Field_validation} message response body"))
def check_field_validation_status(request_context: dict) -> None:
    expected_response_body = {
        "display_message": "Submitted fields are missing or invalid.",
        "error": "FIELD_VALIDATION_ERROR",
        "fields": [
            "status"
        ]
    }
    resp = request_context["response"]
    logging.info(f"POST campaign status change actual response: {json.dumps(resp.json(), indent=4)}")
    assert resp.json() == expected_response_body
