# from typing import TYPE_CHECKING, Optional
#
# from pytest_bdd import scenarios, then, when
# from pytest_bdd.parsers import parse
#
# from db.polaris.models import RetailerConfig
# from tests.step_defs import test_enrolment
#
# scenarios("../features")
#
# if TYPE_CHECKING:
#     from sqlalchemy.orm import Session


# @when(parse("The account holder enrol to {retailer_slug} retailer with all required and all optional fields"))
# def account_holder_enrol_to_retailer_with_all_fields(retailer_config: RetailerConfig, request_context: dict) -> None:
#     test_enrolment.enrol_accountholder_with_all_required_fields(retailer_config, request_context)

# @when(parse("The account holder POST transaction request for {retailer_slug} retailer with {amount:d}"))
# def the_account_holder_transaction_request(retailer_slug: str, amount: int):
#     raise NotImplementedError(
#         u'STEP: And The account holder POST transaction request for trenette retailer with <amount>')
