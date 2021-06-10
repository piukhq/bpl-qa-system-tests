from tests.shared.response_fixtures.base import BaseResponses

SUCCESS: dict = {}

ACCOUNT_HOLDER_ALREADY_EXISTS = {
    "display_message": "It appears this account already exists.",
    "error": "ACCOUNT_EXISTS",
    "fields": ["email"],
}

MISSING_FIELDS = {
    "display_message": "Submitted fields are missing or invalid.",
    "error": "FIELD_VALIDATION_ERROR",
    "fields": ["first_name", "date_of_birth", "phone", "address_line1"],
}

VALIDATION_FAILED = {
    "display_message": "Submitted fields are missing or invalid.",
    "error": "FIELD_VALIDATION_ERROR",
    "fields": ["email", "date_of_birth", "phone", "address_line2", "city"],
}

THIRD_PARTY_IDENTIFIER_VALIDATION_FAILED = {
    "display_message": "Submitted fields are missing or invalid.",
    "error": "FIELD_VALIDATION_ERROR",
    "fields": ["third_party_identifier"],
}


class EnrolResponses(BaseResponses):
    success = SUCCESS
    account_holder_already_exists = ACCOUNT_HOLDER_ALREADY_EXISTS
    missing_fields = MISSING_FIELDS
    validation_failed = VALIDATION_FAILED
    missing_third_party_identifier = THIRD_PARTY_IDENTIFIER_VALIDATION_FAILED
