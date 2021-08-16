import logging
import time
import uuid
from datetime import datetime, timedelta
from pprint import pformat
from typing import List, TYPE_CHECKING

import requests
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

import settings
from db.carina.models import Voucher, VoucherConfig
from db.polaris.models import AccountHolderVoucher
from tests.rewards_rule_management_api.api_requests.base import post_transaction_request
from tests.rewards_rule_management_api.db_actions.campaigns import get_active_campaigns, get_retailer_rewards
from tests.rewards_rule_management_api.response_fixtures.transaction import TransactionResponses
from tests.shared.account_holder import shared_setup_account_holder

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

scenarios("end_to_end/voucher_allocation/")


@given(
    parsers.parse(
        "{retailer_slug} has an active campaign with the slug {campaign_slug} where the earn"
        " increment {earn_inc_is_tx_value} the transaction value"
    )
)
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


@given(parsers.parse("A {status} account holder exists for {retailer_slug}"))
def setup_account_holder(status: str, retailer_slug: str, request_context: dict, polaris_db_session: "Session") -> None:
    retailer, account_holder = shared_setup_account_holder(
        email="automated_test@transaction.test",
        status=status,
        retailer_slug=retailer_slug,
        polaris_db_session=polaris_db_session,
    )

    request_context["account_holder_uuid"] = str(account_holder.id)
    request_context["retailer_slug"] = retailer.slug

    account_holder.current_balances[request_context["campaign"].slug] = {
        "value": 0,
        "campaign_slug": request_context["campaign"].slug,
    }
    flag_modified(account_holder, "current_balances")
    polaris_db_session.commit()


@given(
    parsers.parse(
        "the campaign has an earn rule threshold and a reward goal with the same value for a voucher type"
        " of {voucher_type_slug}"
    )
)
def check_earn_reward_goal(vela_db_session: "Session", voucher_type_slug: str, request_context: dict) -> None:
    assert len(request_context["campaign"].earn_rule_collection) == 1
    earn_rule = request_context["campaign"].earn_rule_collection[0]
    assert len(request_context["campaign"].reward_rule_collection) == 1
    reward_rule = request_context["campaign"].reward_rule_collection[0]
    assert reward_rule.voucher_type_slug == voucher_type_slug
    assert earn_rule.threshold > reward_rule.reward_goal
    request_context["awardable_transaction_value"] = earn_rule.threshold
    request_context["voucher_type_slug"] = voucher_type_slug


@given(parsers.parse("there are unallocated vouchers for the campaign for a voucher type of {voucher_type_slug}"))
def check_or_make_unallocated_vouchers(
    carina_db_session: "Session", polaris_db_session: "Session", voucher_type_slug: str, request_context: dict
) -> None:
    retailer_slug = request_context["retailer_slug"]
    voucher_config = (
        carina_db_session.execute(
            select(VoucherConfig)
            .where(VoucherConfig.retailer_slug == retailer_slug)
            .where(VoucherConfig.voucher_type_slug == voucher_type_slug)
        )
        .scalars()
        .one()
    )
    existing_vouchers = (
        carina_db_session.execute(
            select(Voucher)
            .join(VoucherConfig)
            .where(Voucher.retailer_slug == retailer_slug)  # type: ignore  # "Join" has no attribute "where" (?)
            .where(Voucher.voucher_config == voucher_config)
            .where(Voucher.allocated.is_(False))
        )
        .scalars()
        .all()
    )
    unallocated_voucher_codes = [voucher.voucher_code for voucher in existing_vouchers]
    if (
        len(existing_vouchers) < 5
    ):  # Let's keep enough (5?) spare vouchers knocking about to mitigate against concurrency
        new_vouchers = make_spare_vouchers(carina_db_session, 5 - len(existing_vouchers), retailer_slug, voucher_config)
        unallocated_voucher_codes += [voucher.voucher_code for voucher in new_vouchers]

    request_context["unallocated_voucher_codes"] = unallocated_voucher_codes
    request_context["voucher_config_validity_days"] = voucher_config.validity_days

    # Double check these voucher codes have not been added to the AccountHolderVoucher table
    assert (
        len(
            polaris_db_session.execute(
                # FIXME: BPL-190 will add a unique constraint across voucher_code and retailer at which point this query
                # should probably be updated to filter by retailer too to ensure the correct voucher is retrieved
                select(AccountHolderVoucher).where(AccountHolderVoucher.voucher_code.in_(unallocated_voucher_codes))
            )
            .scalars()
            .all()
        )
        == 0
    )


def make_spare_vouchers(
    carina_db_session: "Session", how_many: int, retailer_slug: str, voucher_config: VoucherConfig
) -> List[Voucher]:
    vouchers = []
    for _ in range(how_many):
        vouchers.append(
            Voucher(
                id=str(uuid.uuid4()),
                voucher_code=str(uuid.uuid4()),
                voucher_config_id=voucher_config.id,
                allocated=False,
                retailer_slug=retailer_slug,
            )
        )
    carina_db_session.bulk_save_objects(vouchers)
    carina_db_session.commit()
    return vouchers


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


# FIXME: This is duplicated from test_transaction.py
@then(parsers.parse("I get a HTTP {status_code:Number} rrm {payload_type} response", extra_types={"Number": int}))
def check_transaction_response_status(status_code: int, payload_type: str, request_context: dict) -> None:
    payload = TransactionResponses.get_json(payload_type)

    assert request_context["resp"].status_code == status_code
    if payload:
        assert request_context["resp"].json() == payload


@then("A voucher is allocated to the account holder")
def check_voucher_allocated(polaris_db_session: "Session", request_context: dict) -> None:
    logging.info(f"Request context:\n{pformat(request_context)}")
    for i in range(5):
        time.sleep(i)
        allocated_vouchers = (
            polaris_db_session.query(AccountHolderVoucher)
            # FIXME: BPL-190 will add a unique constraint across voucher_code and retailer at which point this query
            # should probably be updated to filter by retailer too to ensure the correct voucher is retrieved
            .filter(
                AccountHolderVoucher.voucher_code.in_(request_context["unallocated_voucher_codes"]),
                AccountHolderVoucher.account_holder_id == request_context["account_holder_uuid"],
                AccountHolderVoucher.voucher_type_slug == request_context["voucher_type_slug"],
            ).all()
        )
        if len(allocated_vouchers) == 0:
            continue
        else:
            break
    assert len(allocated_vouchers) == 1
    request_context["allocated_voucher"] = allocated_vouchers[0]


@then("the voucher's expiry date is the correct number of days after the issued date")
def check_voucher_expiry(request_context: dict) -> None:
    voucher = request_context["allocated_voucher"]
    assert voucher.issued_date.date() == datetime.today().date()
    assert voucher.expiry_date - voucher.issued_date == timedelta(days=request_context["voucher_config_validity_days"])


@then("The account holder's balance is updated")
def check_account_holder_balance(request_context: dict) -> None:
    earn_rule = request_context["campaign"].earn_rule_collection[0]
    reward_rule = request_context["campaign"].reward_rule_collection[0]
    retailer_slug = request_context["retailer_slug"]
    account_holder_uuid = request_context["account_holder_uuid"]
    url = f"{settings.POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_uuid}"
    headers = {
        "Authorization": f"token {settings.CUSTOMER_MANAGEMENT_API_TOKEN}",
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
            None,
        )

    for i in range(5):
        time.sleep(i)
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        new_balance = _get_balance(request_context["campaign"].slug, resp.json())
        if new_balance == expected_balance:
            break

    assert new_balance == expected_balance
