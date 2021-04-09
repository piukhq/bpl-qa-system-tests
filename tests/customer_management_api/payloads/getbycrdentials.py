import json
import logging


def all_required_credentials(account_holder):
    payload = {
        "email": account_holder.email,
        "account_number": account_holder.account_number,
    }
    logging.info("`Request body for POST getbycredentials " + json.dumps(payload, indent=4))
    return payload
