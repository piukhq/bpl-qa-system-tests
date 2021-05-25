from tests.shared.response_fixtures.base import BaseResponses

MISSING_FIELDS = [
    {
        "display_message": "Missing credentials from request.",
        "error": "MISSING_FIELDS",
        "fields": ["account_number"],
    }
]

VALIDATION_FAILED = [
    {
        "display_message": "Submitted credentials did not pass validation.",
        "error": "VALIDATION_FAILED",
        "fields": ["email"],
    }
]


class GetByCredentialsResponses(BaseResponses):
    def __init__(self) -> None:
        super().__init__()
        self.missing_fields = MISSING_FIELDS
        self.validation_failed = VALIDATION_FAILED
