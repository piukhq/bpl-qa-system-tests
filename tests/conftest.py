import logging
import uuid

from typing import TYPE_CHECKING, Any, Generator

import pytest

from pytest_bdd import given, parsers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import create_database, database_exists, drop_database

from db.carina.models import Base as CarinaModelBase
from db.carina.models import Reward, RewardConfig
from db.polaris.models import Base as PolarisModelBase
from db.polaris.models import RetailerConfig
from db.vela.models import Base as VelaModelBase
from db.vela.models import Campaign, EarnRule, RetailerRewards, RewardRule
from settings import (
    CARINA_DATABASE_URI,
    CARINA_TEMPLATE_DB_NAME,
    POLARIS_DATABASE_URI,
    POLARIS_TEMPLATE_DB_NAME,
    VELA_DATABASE_URI,
    VELA_TEMPLATE_DB_NAME,
)
from tests.shared_utils.fixture_loader import load_fixture

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import SubRequest
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def polaris_db_session() -> Generator:
    if database_exists(POLARIS_DATABASE_URI):
        logger.info("Dropping Polaris database")
        drop_database(POLARIS_DATABASE_URI)
    logger.info("Creating Polaris database")
    create_database(POLARIS_DATABASE_URI, template=POLARIS_TEMPLATE_DB_NAME)
    engine = create_engine(POLARIS_DATABASE_URI, poolclass=NullPool, echo=False)
    PolarisModelBase.prepare(engine, reflect=True)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session


@pytest.fixture(autouse=True)
def vela_db_session() -> Generator:
    if database_exists(VELA_DATABASE_URI):
        logger.info("Dropping Vela database")
        drop_database(VELA_DATABASE_URI)
    logger.info("Creating Vela database")
    create_database(VELA_DATABASE_URI, template=VELA_TEMPLATE_DB_NAME)
    engine = create_engine(VELA_DATABASE_URI, poolclass=NullPool, echo=False)
    VelaModelBase.prepare(engine, reflect=True)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session


@pytest.fixture(autouse=True)
def carina_db_session() -> Generator:
    if database_exists(CARINA_DATABASE_URI):
        logger.info("Dropping Carina database")
        drop_database(CARINA_DATABASE_URI)
    logger.info("Creating Carina database")
    create_database(CARINA_DATABASE_URI, template=CARINA_TEMPLATE_DB_NAME)
    engine = create_engine(CARINA_DATABASE_URI, poolclass=NullPool, echo=False)
    CarinaModelBase.prepare(engine, reflect=True)
    with sessionmaker(bind=engine)() as db_session:
        yield db_session


# This is the only way I could get the cucumber plugin to work
# in vscode with target_fixture and play nice with flake8
# https://github.com/alexkrechik/VSCucumberAutoComplete/issues/373
# fmt: off
@given(parsers.parse("the {retailer_slug} retailer exists"),
       target_fixture="retailer_config",
       )
# fmt: on
def retailer(polaris_db_session: "Session", vela_db_session: "Session", retailer_slug: str) -> RetailerConfig:
    fixture_data = load_fixture(retailer_slug)
    retailer_config = RetailerConfig(**fixture_data.retailer_config)
    polaris_db_session.add(retailer_config)
    retailer_rewards = RetailerRewards(slug=retailer_slug)
    vela_db_session.add(retailer_rewards)
    polaris_db_session.commit()
    vela_db_session.commit()
    return retailer_config


# fmt: off
@given("has the standard campaigns configured",
       target_fixture="standard_campaigns",
       )
# fmt: on
def standard_campaigns_and_reward_slugs(vela_db_session: "Session", retailer_config: RetailerConfig) -> list[Campaign]:
    fixture_data = load_fixture(retailer_config.slug)
    campaigns: list = []
    for campaign_data in fixture_data.campaign:
        campaign = Campaign(retailer_id=retailer_config.id, **campaign_data)
        vela_db_session.add(campaign)
        vela_db_session.flush()
        campaigns.append(campaign)

        vela_db_session.add_all(
            EarnRule(campaign_id=campaign.id, **earn_rule_data)
            for earn_rule_data in fixture_data.earn_rule.get(campaign.slug, [])
        )

        vela_db_session.add_all(
            RewardRule(campaign_id=campaign.id, **reward_rule_data)
            for reward_rule_data in fixture_data.reward_rule.get(campaign.slug, [])
        )

    vela_db_session.commit()
    return campaigns


# fmt: off
@given(parsers.parse("has the standard reward config configured with {reward_n:d} allocable rewards"),
       target_fixture="standard_reward_configs",
       )
# fmt: on
def standard_reward_and_reward_config(
    carina_db_session: "Session", reward_n: int, retailer_config: RetailerConfig
) -> list[RewardConfig]:
    fixture_data = load_fixture(retailer_config.slug)
    reward_configs: list = []

    for reward_config_data in fixture_data.reward_config:
        reward_config = RewardConfig(**reward_config_data)
        carina_db_session.add(reward_config)
        reward_configs.append(reward_config)

    if reward_n > 0:
        carina_db_session.flush()
        for config in reward_configs:
            carina_db_session.add_all(
                Reward(
                    id=str(uuid.uuid4()),
                    code=f"{config.reward_slug}/{i}",
                    allocated=False,
                    deleted=False,
                    reward_config_id=config.id,
                    retailer_slug=retailer_config.slug,
                )
                for i in range(1, reward_n + 1)
            )

    carina_db_session.commit()
    return reward_configs


# Hooks
def pytest_bdd_step_error(
    request: Any,
    feature: Any,
    scenario: Any,
    step: Any,
    step_func: Any,
    step_func_args: Any,
    exception: Any,
) -> None:
    """This function will log the failed BDD-Step at the end of logs"""
    logging.info(f"Step failed: {step}")


def pytest_html_report_title(report: Any) -> None:
    """Customized title for html report"""
    report.title = "BPL QA System Automation Results"


@pytest.fixture(scope="function")
def request_context() -> dict:
    return {}


@pytest.fixture(scope="session", autouse=True)
def configure_html_report_env(request: "SubRequest", env: str, channel: str) -> None:
    """Delete existing data in the test report and add bpl execution details"""

    metadata: dict = getattr(request.config, "_metadata")

    for ele in list(metadata.keys()):
        del metadata[ele]
    # if re.search(r'^(GITLAB_|CI_)', k): for git lab related extra table contents
    metadata.update({"Test Environment": env.upper(), "Channel": channel})


def pytest_addoption(parser: "Parser") -> None:
    parser.addoption("--env", action="store", default="staging", help="env : can be dev or staging or prod")
    parser.addoption("--channel", action="store", default="user-channel", help="env : can be dev or staging or prod")


@pytest.fixture(scope="session")
def env(pytestconfig: "Config") -> Generator:
    """Returns current environment"""
    return pytestconfig.getoption("env")


@pytest.fixture(scope="session")
def channel(pytestconfig: "Config") -> Generator:
    """Returns current environment"""
    return pytestconfig.getoption("channel")
