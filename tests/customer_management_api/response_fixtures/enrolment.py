
SUCCESS = {}

INVALID_MERCHANT = {
  "display_message": "Requested retailer is invalid.",
  "error": "INVALID_RETAILER"
}

USER_ALREADY_EXISTS = {
  "display_message": "There is already an account with that email address",
  "error": "ACCOUNT_EXISTS",
  "fields": [
    "email"
  ]
}


class EnrolResponses:

    def __init__(self):
        self.success = SUCCESS
        self.invalid_merchant = INVALID_MERCHANT
        self.user_already_exists = USER_ALREADY_EXISTS

    def get_json(self, key: str) -> dict:
        key = key.lower()
        try:
            return getattr(self, key)
        except AttributeError as e:
            raise AttributeError(f"Missing response fixture: {key}, please add it to: {__name__}") from e
