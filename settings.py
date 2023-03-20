import logging
import os
import typing as t

from collections.abc import Callable

from dotenv import load_dotenv
from redis import Redis

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

HUBBLE_DATABASE_URI = getenv("HUBBLE_DATABASE_URI")
HUBBLE_TEMPLATE_DB_NAME = getenv("HUBBLE_TEMPLATE_DB_NAME")

COSMOS_DATABASE_URI = getenv("COSMOS_DATABASE_URI")
COSMOS_TEMPLATE_DB_NAME = getenv("COSMOS_TEMPLATE_DB_NAME")

VAULT_URL = getenv("VAULT_URL")
vault = KeyVault(VAULT_URL)

CAMPAIGN_API_AUTH_TOKEN = vault.get_secret("bpl-campaigns-api-auth-token")
TX_API_AUTH_TOKEN = vault.get_secret("bpl-transactions-api-auth-token")
ACCOUNT_API_AUTH_TOKEN = vault.get_secret("bpl-accounts-api-auth-token")

LOCAL = getenv("LOCAL", default="False", conv=boolconv)

BLOB_STORAGE_DSN = getenv("BLOB_STORAGE_DSN")
REPORT_CONTAINER = getenv("REPORT_CONTAINER", default="qareports")
REPORT_DIRECTORY = getenv("REPORT_DIRECTORY", default="bpl/isolated/")
BLOB_IMPORT_CONTAINER = getenv("BLOB_IMPORT_CONTAINER", "cosmos-imports")
BLOB_ARCHIVE_CONTAINER = getenv("BLOB_ARCHIVE_CONTAINER", "cosmos-archive")
BLOB_ERROR_CONTAINER = getenv("BLOB_ERROR_CONTAINER", "cosmos-errors")

TEAMS_WEBHOOK = getenv("TEAMS_WEBHOOK") if not LOCAL else None
FRIENDLY_NAME = getenv("FRIENDLY_NAME", default="BPL")
SCHEDULE = getenv("SCHEDULE")
COMMAND = getenv("COMMAND", default="pytest -m bpl")
ALERT_ON_SUCCESS = getenv("ALERT_ON_SUCCESS", default="True", conv=boolconv)
ALERT_ON_FAILURE = getenv("ALERT_ON_FAILURE", default="True", conv=boolconv)

ACCOUNTS_API_BASE_URL = getenv("ACCOUNTS_ENV_API_BASE_URL")
TRANSACTIONS_API_BASE_URL = getenv("TRANSACTIONS_ENV_API_BASE_URL")
CAMPAIGNS_API_BASE_URL = getenv("CAMPAIGNS_ENV_API_BASE_URL")
PUBLIC_API_BASE_URL = getenv("PUBLIC_ENV_API_BASE_URL")

MOCK_SERVICE_BASE_URL = getenv("MOCK_SERVICE_BASE_URL")

REDIS_URL = getenv("REDIS_URL")

API_REFLECTOR_BASE_URL = getenv("API_REFLECTOR_BASE_URL", "https://reflector.staging.gb.bink.com/mock")
SQL_DEBUG = bool(getenv("SQL_DEBUG", "False") in ["True", "true"])

redis = Redis.from_url(
    REDIS_URL,
    socket_connect_timeout=3,
    socket_keepalive=True,
    retry_on_timeout=False,
    decode_responses=True,
)
