from tests.shared_utils.response_fixtures.errors import (
    INVALID_RETAILER,
    INVALID_TOKEN,
    MALFORMED_REQUEST,
    MISSING_CHANNEL_HEADER,
    NO_ACCOUNT_FOUND,
    INVALID_STATUS_REQUESTED,
    NO_CAMPAIGN_FOUND,
)


class BaseResponses:
    invalid_retailer = INVALID_RETAILER
    no_account_found = NO_ACCOUNT_FOUND
    malformed_request = MALFORMED_REQUEST
    invalid_token = INVALID_TOKEN
    missing_channel_header = MISSING_CHANNEL_HEADER
    invalid_status_requested = INVALID_STATUS_REQUESTED
    no_campaign_found = NO_CAMPAIGN_FOUND

    @classmethod
    def get_json(cls, key: str) -> dict:
        key = key.lower()

        try:
            return getattr(cls, key)
        except AttributeError as e:
            raise AttributeError(f"Missing response fixture: {key}, " f"please add it to: {cls.__name__}") from e
