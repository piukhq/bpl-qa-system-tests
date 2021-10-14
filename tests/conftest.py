import logging

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generator

import pytest

from db.carina.session import CarinaSessionMaker
from db.polaris.session import PolarisSessionMaker
from db.vela.models import Campaign, CampaignStatuses, RetailerRewards
from db.vela.session import VelaSessionMaker

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


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
    report.title = "BPL Test Automation Results"


@pytest.fixture(scope="function")
def request_context() -> dict:
    return {}


@pytest.fixture(scope="function")
def carina_db_session() -> Generator:
    with CarinaSessionMaker() as db_session:
        yield db_session


@pytest.fixture(scope="function")
def polaris_db_session() -> Generator:
    with PolarisSessionMaker() as db_session:
        yield db_session


@pytest.fixture(scope="function")
def vela_db_session() -> Generator:
    with VelaSessionMaker() as db_session:
        yield db_session


@pytest.fixture(scope="function")
def create_mock_campaign(vela_db_session: "Session") -> Generator:
    mock_campaign: Campaign = None

    mock_campaign_params = {
        "status": CampaignStatuses.ACTIVE,
        "name": "testcampaign",
        "slug": "test-campaign",
        "start_date": datetime.utcnow() - timedelta(minutes=5),
        "earn_inc_is_tx_value": True,
    }

    def _create_mock_campaign(retailer: RetailerRewards, **campaign_params: dict) -> Campaign:
        """
        Create a campaign in the DB
        :param campaign_params: override any values for the campaign, from what the default dict provides
        :return: Callable function
        """

        mock_campaign_params.update(campaign_params)  # type: ignore
        nonlocal mock_campaign
        mock_campaign = Campaign(**mock_campaign_params, retailer_id=retailer.id)
        vela_db_session.add(mock_campaign)
        vela_db_session.commit()

        return mock_campaign

    yield _create_mock_campaign

    vela_db_session.delete(mock_campaign)
    vela_db_session.commit()
