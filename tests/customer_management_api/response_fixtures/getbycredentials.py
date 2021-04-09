INVALID_RETAILER = {
    "display_message": "Requested retailer is invalid.",
    "error": "INVALID_RETAILER"
}

INVALID_TOKEN = {
    "display_message": "Supplied token is invalid.",
    "error": "INVALID_TOKEN"
}

MISSING_FIELDS = [
    {
        "display_message": "Missing credentials from request.",
        "error": "MISSING_FIELDS",
        "fields": [
            "email"
        ]
    }
]

MALFORMED_REQUEST = {
    "display_message": "Malformed request.",
    "error": "MALFORMED_REQUEST"
}

VALIDATION_FAILED = [
    {
        "display_message": "Submitted credentials did not pass validation.",
        "error": "VALIDATION_FAILED",
        "fields": [
            "email"
        ]
    }
]

NO_ACCOUNT_FOUND = {
    "display_message": "Account not found for provided credentials",
    "error": "NO_ACCOUNT_FOUND",
}


class GetByCredentialsResponses:

    def __init__(self):
        self.invalid_retailer = INVALID_RETAILER
        self.no_account_found = NO_ACCOUNT_FOUND
        self.malformed_request = MALFORMED_REQUEST
        self.missing_fields = MISSING_FIELDS
        self.invalid_token = INVALID_TOKEN
        self.validation_failed = VALIDATION_FAILED

    def get_json(self, key: str) -> dict:
        key = key.lower()

        try:
            return getattr(self, key)
        except AttributeError as e:
            raise AttributeError(f"Missing response fixture: {key}, please add it to: {__name__}") from e
