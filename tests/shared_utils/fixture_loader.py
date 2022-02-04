from datetime import datetime, timedelta, timezone

import yaml


def _generate_datetime(loader: yaml.loader.SafeLoader, node: yaml.nodes.MappingNode) -> str:
    params = loader.construct_mapping(node)
    now = datetime.now(tz=timezone.utc)
    if "timedelta" in params:
        time = now + timedelta(days=params["timedelta"])
    else:
        time = now

    return time.isoformat()


def _yaml_as_string(loader: yaml.loader.SafeLoader, node: yaml.nodes.MappingNode) -> str:
    content = loader.construct_mapping(node, deep=True)
    return yaml.dump(content, indent=2)


yaml.add_constructor("!utc_now", _generate_datetime)
yaml.add_constructor("!as_yaml_string", _yaml_as_string)


def load_fixture(project_name: str, fixture_name: str) -> dict:
    with open(f"tests/fixtures/{project_name}.yaml", "r") as f:
        fixture = yaml.load(f)

    return fixture.get(fixture_name, {})


# if __name__ == "__main__":
# from pprint import pprint

# print("RetailerConfig")
# pprint(load_fixture("polaris", "retailer_config"))
# print("\nCampaign")
# pprint(load_fixture("vela", "campaign"))
