from tests.shared_utils.response_fixtures.base import BaseResponses

UNKNOWN_VOUCHER_TYPE = {"display_message": "Voucher Type Slug does not exist.", "error": "UNKNOWN_VOUCHER_TYPE"}


class VoucherAllocationResponses(BaseResponses):
    unknown_voucher_type = UNKNOWN_VOUCHER_TYPE
