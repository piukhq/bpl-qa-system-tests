INVALID_RETAILER = {
    "display_message": "Requested retailer is invalid.",
    "code": "INVALID_RETAILER",
}

INVALID_TOKEN = {
    "display_message": "Supplied token is invalid.",
    "code": "INVALID_TOKEN",
}

MALFORMED_REQUEST = {
    "display_message": "Malformed request.",
    "code": "MALFORMED_REQUEST",
}

NO_ACCOUNT_FOUND = {
    "display_message": "Account not found for provided credentials.",
    "code": "NO_ACCOUNT_FOUND",
}

MISSING_CHANNEL_HEADER = {
    "display_message": "Submitted headers are missing or invalid.",
    "code": "HEADER_VALIDATION_ERROR",
    "fields": [
        "bpl-user-channel",
    ],
}

INVALID_STATUS_REQUESTED = {
    "display_message": "The requested status change could not be performed.",
    "code": "INVALID_STATUS_REQUESTED",
}

NO_CAMPAIGN_FOUND = {
    "display_message": "Campaign not found for provided slug.",
    "code": "NO_CAMPAIGN_FOUND",
}

DUPLICATE_TRANSACTION = {
    "display_message": "Duplicate Transaction.",
    "code": "DUPLICATE_TRANSACTION",
}

USER_NOT_FOUND = {
    "display_message": "Unknown User.",
    "code": "USER_NOT_FOUND",
}

USER_NOT_ACTIVE = {
    "display_message": "User Account not Active",
    "code": "USER_NOT_ACTIVE",
}

INVALID_CONTENT = {
    "display_message": "BPL Schema not matched.",
    "code": "INVALID_CONTENT",
}


NO_ACTIVE_CAMPAIGNS = {
    "display_message": "No active campaigns found for retailer.",
    "code": "NO_ACTIVE_CAMPAIGNS",
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
