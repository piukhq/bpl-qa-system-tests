from tests.shared_utils.response_fixtures.base import BaseResponses

MISSING_FIELDS = {
    "display_message": "Submitted fields are missing or invalid.",
    "error": "FIELD_VALIDATION_ERROR",
    "fields": ["account_number"],
}

VALIDATION_FAILED = {
    "display_message": "Submitted fields are missing or invalid.",
    "error": "FIELD_VALIDATION_ERROR",
    "fields": ["email"],
}


class GetByCredentialsResponses(BaseResponses):
    missing_fields = MISSING_FIELDS
    validation_failed = VALIDATION_FAILED
