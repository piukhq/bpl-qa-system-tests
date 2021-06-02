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


class TransactionResponses:
    invalid_retailer = INVALID_RETAILER
    user_not_active = USER_NOT_ACTIVE
    malformed_request = MALFORMED_REQUEST
    invalid_token = INVALID_TOKEN
    duplicate_transaction = DUPLICATE_TRANSACTION
    user_not_found = USER_NOT_FOUND
    invalid_content = INVALID_CONTENT
    # TODO: adapt success response when the correct one is implemented in vela
    success = None

    @classmethod
    def get_json(cls, key: str) -> dict:
        key = key.lower()

        try:
            return getattr(cls, key)
        except AttributeError as e:
            raise AttributeError(f"Missing response fixture: {key}, " f"please add it to: {cls.__name__}") from e
