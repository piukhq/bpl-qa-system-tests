import logging

from typing import TYPE_CHECKING, Generator

import pytest

from pytest_bdd import given, parsers
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import create_database, database_exists, drop_database

from db.carina.models import Base as CarinaModelBase
from db.polaris.models import Base as PolarisModelBase
from db.polaris.models import RetailerConfig
from db.vela.models import Base as VelaModelBase
from db.vela.models import Campaign, RetailerRewards
from settings import (
    CARINA_DATABASE_URI,
    CARINA_TEMPLATE_DB_NAME,
    POLARIS_DATABASE_URI,
    POLARIS_TEMPLATE_DB_NAME,
    VELA_DATABASE_URI,
    VELA_TEMPLATE_DB_NAME,
)
from tests.retailer_data import RETAILER_DATA

if TYPE_CHECKING:
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


@pytest.fixture
def retailer_data() -> dict:
    return RETAILER_DATA


# This is the only way I could get the cucumber plugin to work
# in vscode with target_fixture and play nice with flake8
# https://github.com/alexkrechik/VSCucumberAutoComplete/issues/373
# fmt: off
@given(parsers.parse("the {retailer_slug} retailer exists"),
       target_fixture="retailer_config",
       )
# fmt: on
def retailer(
    polaris_db_session: "Session", vela_db_session: "Session", retailer_slug: str, retailer_data: dict
) -> RetailerConfig:
    retailer_config = RetailerConfig(
        slug=retailer_slug,
        name=retailer_data[retailer_slug]["name"],
        account_number_prefix=retailer_data[retailer_slug]["account_number_prefix"],
        profile_config=retailer_data[retailer_slug]["profile_config"],
        marketing_preference_config=retailer_data[retailer_slug]["marketing_preference_config"],
        loyalty_name=retailer_data[retailer_slug]["loyalty_name"],
        welcome_email_from="potato@potato.com",
        welcome_email_subject="potato",
    )
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
def standard_campaigns(
    # FIXME This needs completing: earn/reward rules etc
    vela_db_session: "Session",
    retailer_config: RetailerConfig,
    retailer_data: dict,
) -> dict[str, Campaign]:
    campaigns: dict[str, Campaign] = {}
    for campaign_data in retailer_data[retailer_config.slug]["default_campaigns"]:
        campaign = Campaign(retailer_id=retailer_config.id, **campaign_data)
        vela_db_session.add(campaign)
        campaigns[campaign.slug] = campaign
    vela_db_session.commit()
    return campaigns
