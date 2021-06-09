from tests.shared.response_fixtures.base import BaseResponses

SUCCESS: dict = {}

MISSING_FIELDS = [
    {
        "display_message": "Missing credentials from request.",
        "error": "MISSING_FIELDS",
        "fields": ["first_name", "date_of_birth", "phone", "address_line1"],
    }
]

ACCOUNT_HOLDER_ALREADY_EXISTS = {
    "display_message": "It appears this account already exists.",
    "error": "ACCOUNT_EXISTS",
    "fields": ["email"],
}

VALIDATION_FAILED = [
    {
        "display_message": "Submitted credentials did not pass validation.",
        "error": "VALIDATION_FAILED",
        "fields": ["email", "date_of_birth", "phone", "address_line2", "city"],
    }
]

THIRD_PARTY_IDENTIFIER_VALIDATION_FAILED = [
    {
        "display_message": "Missing credentials from request.",
        "error": "MISSING_FIELDS",
        "fields": ["third_party_identifier"],
    }
]


class EnrolResponses(BaseResponses):
    success = SUCCESS
    account_holder_already_exists = ACCOUNT_HOLDER_ALREADY_EXISTS
    missing_fields = MISSING_FIELDS
    validation_failed = VALIDATION_FAILED
    missing_third_party_identifier = THIRD_PARTY_IDENTIFIER_VALIDATION_FAILED
