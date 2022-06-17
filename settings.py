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

CARINA_DATABASE_URI = getenv("CARINA_DATABASE_URI")
POLARIS_DATABASE_URI = getenv("POLARIS_DATABASE_URI")
VELA_DATABASE_URI = getenv("VELA_DATABASE_URI")
CARINA_TEMPLATE_DB_NAME = getenv("CARINA_TEMPLATE_DB_NAME")
POLARIS_TEMPLATE_DB_NAME = getenv("POLARIS_TEMPLATE_DB_NAME")
VELA_TEMPLATE_DB_NAME = getenv("VELA_TEMPLATE_DB_NAME")

VAULT_URL = getenv("VAULT_URL")
vault = KeyVault(VAULT_URL)
POLARIS_API_AUTH_TOKEN = vault.get_secret("bpl-polaris-api-auth-token")
VELA_API_AUTH_TOKEN = vault.get_secret("bpl-vela-api-auth-token")
CARINA_API_AUTH_TOKEN = vault.get_secret("bpl-carina-api-auth-token")

LOCAL = getenv("LOCAL", default="False", conv=boolconv)

BLOB_STORAGE_DSN = getenv("BLOB_STORAGE_DSN")
REPORT_CONTAINER = getenv("REPORT_CONTAINER", default="qareports")
REPORT_DIRECTORY = getenv("REPORT_DIRECTORY", default="bpl/isolated/")
BLOB_IMPORT_CONTAINER = "carina-imports"
BLOB_ARCHIVE_CONTAINER = "carina-archive"
BLOB_ERROR_CONTAINER = "carina-errors"

TEAMS_WEBHOOK = getenv("TEAMS_WEBHOOK") if not LOCAL else None
FRIENDLY_NAME = getenv("FRIENDLY_NAME", default="BPL")
SCHEDULE = getenv("SCHEDULE")
COMMAND = getenv("COMMAND", default="pytest -m bpl")
ALERT_ON_SUCCESS = getenv("ALERT_ON_SUCCESS", default="True", conv=boolconv)
ALERT_ON_FAILURE = getenv("ALERT_ON_FAILURE", default="True", conv=boolconv)

CARINA_BASE_URL = getenv("CARINA_ENV_BASE_URL")
POLARIS_BASE_URL = getenv("POLARIS_ENV_BASE_URL")
VELA_BASE_URL = getenv("VELA_ENV_BASE_URL")

MOCK_SERVICE_BASE_URL = getenv("MOCK_SERVICE_BASE_URL")

REDIS_URL = getenv("REDIS_URL")

API_BASE_URL = "https://reflector.staging.gb.bink.com/mock"

redis = Redis.from_url(
    REDIS_URL,
    socket_connect_timeout=3,
    socket_keepalive=True,
    retry_on_timeout=False,
    decode_responses=True,
)
