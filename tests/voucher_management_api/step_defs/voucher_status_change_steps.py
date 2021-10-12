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

    return retry_session().patch(
        f"{CARINA_BASE_URL}/{retailer_slug}/vouchers/{voucher_type_slug}/status",
        json=request_body,
        headers=headers or default_headers,
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


@then(parse("the status of the voucher config is {new_status}"))
def check_voucher_config_status(carina_db_session: "Session", new_status: str, request_context: dict) -> None:
    voucher_config_status = carina_db_session.execute(
        select(VoucherConfig.status).where(VoucherConfig.id == request_context["voucher_config_id"])
    ).scalar()
    assert voucher_config_status == new_status, f"{voucher_config_status} != {new_status}"
