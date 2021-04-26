from .shared import INVALID_RETAILER, INVALID_TOKEN, MALFORMED_REQUEST, MISSING_CHANNEL_HEADER, VALIDATION_FAILED

SUCCESS: dict = {}

MISSING_FIELDS = [
    {
        "display_message": "Missing credentials from request.",
        "error": "MISSING_FIELDS",
        "fields": ["first_name"],
    }
]

ACCOUNT_HOLDER_ALREADY_EXISTS = {
    "display_message": "It appears this account already exists.",
    "error": "ACCOUNT_EXISTS",
    "fields": ["email"],
}


class EnrolResponses:
    def __init__(self) -> None:
        self.success = SUCCESS
        self.invalid_retailer = INVALID_RETAILER
        self.account_holder_already_exists = ACCOUNT_HOLDER_ALREADY_EXISTS
        self.malformed_request = MALFORMED_REQUEST
        self.missing_fields = MISSING_FIELDS
        self.invalid_token = INVALID_TOKEN
        self.validation_failed = VALIDATION_FAILED
        self.missing_channel_header = MISSING_CHANNEL_HEADER

    def get_json(self, key: str) -> dict:
        key = key.lower()
        try:
            return getattr(self, key)
        except AttributeError as e:
            raise AttributeError(f"Missing response fixture: {key}, please add it to: {__name__}") from e
