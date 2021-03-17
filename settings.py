import logging
import os
import typing as t
from collections.abc import Callable

from azure.vault import KeyVault


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


logging.basicConfig(format="%(process)s %(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("bpl_automation_tests_logger")
log_level = getenv("LOG_LEVEL", default="DEBUG")
logger.setLevel(log_level)

SQLALCHEMY_DATABASE_URI = getenv("SQLALCHEMY_DATABASE_URI")

VAULT_URL = getenv("VAULT_URL")

USE_BLOB_STORAGE = getenv("USE_BLOB_STORAGE", default="True", conv=boolconv)
BLOB_STORAGE_DSN = getenv("BLOB_STORAGE_DSN") if USE_BLOB_STORAGE else None
REPORT_CONTAINER = getenv("REPORT_CONTAINER", default="qareports")
REPORT_DIRECTORY = getenv("REPORT_DIRECTORY", default="bpl/isolated/")

vault = KeyVault(VAULT_URL)


class Secrets:
    test_merchant_auth_secret = vault.get_secret("bpl-customer-mgmt-auth-token")
