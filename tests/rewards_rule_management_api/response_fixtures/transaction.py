from tests.shared.response_fixtures.errors import INVALID_RETAILER, INVALID_TOKEN, MALFORMED_REQUEST

DUPLICATE_TRANSACTION = {
    "display_message": "Duplicate Transaction.",
    "error": "DUPLICATE_TRANSACTION",
}

USER_NOT_FOUND = {
    "display_message": "Unknown User.",
    "error": "USER_NOT_FOUND",
}

USER_NOT_ACTIVE = {
    "display_message": "User Account not Active",
    "error": "USER_NOT_ACTIVE",
}

INVALID_CONTENT = {
    "display_message": "BPL Schema not matched.",
    "error": "INVALID_CONTENT",
}


NO_ACTIVE_CAMPAIGNS = {
    "display_message": "No active campaigns found for retailer.",
    "error": "NO_ACTIVE_CAMPAIGNS",
}


class TransactionResponses:
    invalid_retailer = INVALID_RETAILER
    user_not_active = USER_NOT_ACTIVE
    malformed_request = MALFORMED_REQUEST
    invalid_token = INVALID_TOKEN
    duplicate_transaction = DUPLICATE_TRANSACTION
    user_not_found = USER_NOT_FOUND
    invalid_content = INVALID_CONTENT
    no_active_campaigns = NO_ACTIVE_CAMPAIGNS
    # TODO: adapt success response when the correct one is implemented in vela
    awarded = "Awarded"
    threshold_not_met = "Threshold not met"

    @classmethod
    def get_json(cls, key: str) -> dict:
        key = key.lower()

        try:
            return getattr(cls, key)
        except AttributeError as e:
            raise AttributeError(f"Missing response fixture: {key}, " f"please add it to: {cls.__name__}") from e
