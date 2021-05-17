import logging
import os
import typing as t

from collections.abc import Callable

from dotenv import load_dotenv

from azure_actions.vault import KeyVault


class ConfigVarRequiredError(Exception):
    pass


def getenv(key: str, default: str = None, conv: Callable[[str], t.Any] = str, required: bool = True) -> t.Any:
    """If `default` is None, then the var is non-optional."""
    var = os.getenv(key, default)
    if var is None and required is True:
        raise ConfigVarRequiredError(f"Configuration variable '{key}' is required but was not provided.")
    elif var is not None:
        return conv(var)
    else:
        return None


def boolconv(s: str) -> bool:
    return s.lower() in ["true", "t", "yes"]


load_dotenv()

logger = logging.getLogger("bpl_automation_tests_logger")
logger.setLevel(logging.DEBUG)

SQLALCHEMY_DATABASE_URI = getenv("SQLALCHEMY_DATABASE_URI")

VAULT_URL = getenv("VAULT_URL")
vault = KeyVault(VAULT_URL)
CUSTOMER_MANAGEMENT_API_TOKEN = vault.get_secret("bpl-customer-mgmt-auth-token")

LOCAL = getenv("LOCAL", default="False", conv=boolconv)

BLOB_STORAGE_DSN = getenv("BLOB_STORAGE_DSN") if not LOCAL else None
REPORT_CONTAINER = getenv("REPORT_CONTAINER", default="qareports")
REPORT_DIRECTORY = getenv("REPORT_DIRECTORY", default="bpl/isolated/")

TEAMS_WEBHOOK = getenv("TEAMS_WEBHOOK") if not LOCAL else None
FRIENDLY_NAME = getenv("FRIENDLY_NAME", default="BPL")
SCHEDULE = getenv("SCHEDULE")
COMMAND = getenv("COMMAND", default="pytest -m bpl")
ALERT_ON_SUCCESS = getenv("ALERT_ON_SUCCESS", default="True", conv=boolconv)
ALERT_ON_FAILURE = getenv("ALERT_ON_FAILURE", default="True", conv=boolconv)

ENV_BASE_URL = getenv("ENV_BASE_URL")
MOCK_SERVICE_BASE_URL = getenv("MOCK_SERVICE_BASE_URL")

# n.b. this has to be the kubernetes internal url.
POLARIS_URL = getenv("POLARIS_URL", "http://polaris-api")
