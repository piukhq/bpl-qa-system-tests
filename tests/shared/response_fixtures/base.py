from tests.shared.response_fixtures.errors import (
    INVALID_RETAILER,
    INVALID_TOKEN,
    MALFORMED_REQUEST,
    MISSING_CHANNEL_HEADER,
    NO_ACCOUNT_FOUND,
)


class BaseResponses:
    def __init__(self) -> None:
        self.invalid_retailer = INVALID_RETAILER
        self.no_account_found = NO_ACCOUNT_FOUND
        self.malformed_request = MALFORMED_REQUEST
        self.invalid_token = INVALID_TOKEN
        self.missing_channel_header = MISSING_CHANNEL_HEADER

    def get_json(self, key: str) -> dict:
        key = key.lower()

        try:
            return getattr(self, key)
        except AttributeError as e:
            raise AttributeError(
                f"Missing response fixture: {key}, " f"please add it to: {self.__class__.__name__}"
            ) from e
