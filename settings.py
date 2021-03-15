import logging
import os
import typing as t
from collections.abc import Callable


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
BLOB_STORAGE_DSN = getenv("BLOB_STORAGE_DSN")
