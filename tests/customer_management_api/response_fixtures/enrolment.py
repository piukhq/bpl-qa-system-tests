SUCCESS = {}

INVALID_RETAILER = {
    "display_message": "Requested retailer is invalid.",
    "error": "INVALID_RETAILER"
}

INVALID_TOKEN = {
    "display_message": "Supplied token is invalid.",
    "error": "INVALID_TOKEN"
}

ACCOUNT_HOLDER_ALREADY_EXISTS = {
    "display_message": "It appears this account already exists.",
    "error": "ACCOUNT_EXISTS",
    "fields": [
        "email"
    ]
}

MISSING_FIELDS = [
  {
    "display_message": "Missing credentials from request.",
    "error": "MISSING_FIELDS",
    "fields": [
      "first_name"
    ]
  }
]

MALFORMED_REQUEST = {
    "display_message": "Malformed request.",
    "error": "MALFORMED_REQUEST"
}

VALIDATION_FAILED_REQUEST = [
    {
        "display_message": "Submitted credentials did not pass validation.",
        "error": "VALIDATION_FAILED",
        "fields": [
            "email"
        ]
    }
]

MISSING_CHANNEL_HEADER = {
    "display_message": "Missing header",
    "error": "MISSING_HTTP_HEADER",
    "fields": [
        "Bpl-User-Channel",
    ],
}


class EnrolResponses:

    def __init__(self):
        self.success = SUCCESS
        self.invalid_retailer = INVALID_RETAILER
        self.account_holder_already_exists = ACCOUNT_HOLDER_ALREADY_EXISTS
        self.malformed_request = MALFORMED_REQUEST
        self.missing_fields = MISSING_FIELDS
        self.invalid_token = INVALID_TOKEN
        self.validation_failed = VALIDATION_FAILED_REQUEST
        self.missing_channel_header = MISSING_CHANNEL_HEADER

    def get_json(self, key: str) -> dict:
        key = key.lower()
        try:
            return getattr(self, key)
        except AttributeError as e:
            raise AttributeError(f"Missing response fixture: {key}, please add it to: {__name__}") from e
