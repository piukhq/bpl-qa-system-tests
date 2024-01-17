import logging
import uuid

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import TYPE_CHECKING, Union

import yaml

from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from yaml.loader import FullLoader, Loader, UnsafeLoader
    from yaml.nodes import Node


class FixtureData(BaseModel):
    retailer_config: dict
    campaign: list[dict]
    earn_rule: dict[str, list[dict]]
    reward_rule: dict[str, list[dict]]
    reward_config: dict[str, list[dict]]
    retailer_fetch_type: dict

    class Config:
        extra = "forbid"


def _generate_datetime(loader: Union["FullLoader", "Loader", "UnsafeLoader"], node: "Node") -> str:
    params = loader.construct_mapping(node)  # type: ignore [arg-type]
    now = datetime.now(tz=timezone.utc)
    if "timedelta" in params:
        time = now + timedelta(days=params["timedelta"])
    else:
        time = now

    return time.isoformat()


def _yaml_as_string(loader: Union["FullLoader", "Loader", "UnsafeLoader"], node: "Node") -> str:
    content = loader.construct_mapping(node, deep=True)  # type: ignore [arg-type]
    return yaml.dump(content, indent=2)


def _generate_uuid(loader: Union["FullLoader", "Loader", "UnsafeLoader"], node: "Node") -> str:
    return str(uuid.uuid4())


yaml.add_constructor("!utc_now", _generate_datetime)
yaml.add_constructor("!as_yaml_string", _yaml_as_string)
yaml.add_constructor("!uuid4", _generate_uuid)


@lru_cache
def load_fixture(retailer_slug: str) -> FixtureData:
    try:
        with open(f"tests/fixtures/{retailer_slug}.yaml", "r") as f:
            fixture = yaml.full_load(f)

        return FixtureData(**fixture)

    except FileNotFoundError:
        raise ValueError(f"Fixture file '{retailer_slug}.yaml' not found in the fixtures folder.")

    except ValidationError as err:
        msg = f"\nFailed to load '{retailer_slug}.yaml': "
        err_types: dict = {}

        for error in err.args[0]:
            err_msg = error.exc.msg_template
            if err_msg in err_types:
                err_types[err_msg].append(error._loc)
            else:
                err_types[err_msg] = [error._loc]

        for err_name, err_value in err_types.items():
            msg += f"\n - {err_name}: {err_value}"

        logging.error(msg)
        raise
