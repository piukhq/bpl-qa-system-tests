from tests.shared_utils.response_fixtures.base import BaseResponses


class VoucherStatusResponses(BaseResponses):
    no_voucher_found = {
        "display_message": "Voucher not found.",
        "error": "NO_VOUCHER_FOUND",
    }
    status_not_changed = {
        "display_message": "Voucher status incorrect.",
        "error": "STATUS_NOT_CHANGED",
    }
    invalid_status = {
        "display_message": "Status Rejected.",
        "error": "INVALID_STATUS",
    }
    success: dict = {}
