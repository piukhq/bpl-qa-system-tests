import logging
import uuid

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Generator, Optional

import pytest

from sqlalchemy import delete

from db.carina.models import Rewards, RewardConfig
from db.carina.session import CarinaSessionMaker
from db.polaris.session import PolarisSessionMaker
from db.vela.models import Campaign, CampaignStatuses, RetailerRewards, RewardRule
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
    mock_campaigns_ids: list[int] = []

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
        nonlocal mock_campaigns_ids

        mock_campaign_params.update(campaign_params)
        mock_campaign = Campaign(**mock_campaign_params, retailer_id=retailer.id)
        vela_db_session.add(mock_campaign)
        vela_db_session.commit()

        mock_campaigns_ids.append(mock_campaign.id)
        return mock_campaign

    yield _create_mock_campaign

    vela_db_session.execute(delete(Campaign).where(Campaign.id.in_(mock_campaigns_ids)))
    vela_db_session.commit()


@pytest.fixture(scope="function")
def create_config_and_vouchers(carina_db_session: "Session") -> Generator:
    voucher_config: Optional[RewardConfig] = None

    def fn(
        retailer_slug: str, voucher_type_slug: str, status: Optional[str] = "ACTIVE", num_vouchers: int = 5
    ) -> RewardConfig:
        nonlocal voucher_config
        voucher_config = RewardConfig(
            retailer_slug=retailer_slug,
            voucher_type_slug=voucher_type_slug,
            validity_days=1,
            fetch_type="PRE_LOADED",
            status=status,
        )
        carina_db_session.add(voucher_config)
        carina_db_session.commit()

        voucher_ids = [str(uuid.uuid4()) for i in range(num_vouchers)]
        carina_db_session.add_all(
            [
                Rewards(
                    id=voucher_id,
                    retailer_slug=retailer_slug,
                    voucher_config_id=voucher_config.id,
                    voucher_code=str(voucher_id),
                    allocated=False,
                    deleted=False,
                )
                for voucher_id in voucher_ids
            ]
        )
        carina_db_session.commit()

        return voucher_config, voucher_ids

    yield fn

    if voucher_config:
        carina_db_session.execute(delete(Rewards).where(Rewards.voucher_config_id == voucher_config.id))
        carina_db_session.delete(voucher_config)
        carina_db_session.commit()


@pytest.fixture(scope="function")
def create_mock_retailer(vela_db_session: "Session") -> Generator:
    mock_retailer: RetailerRewards = None

    mock_retailer_params = {
        "slug": "automated-test-retailer",
    }

    def _create_mock_retailer(**retailer_params: dict) -> RetailerRewards:
        """
        Create a retailer in the Vela DB
        :param retailer_params: override any values for the retailer, from what the default dict provides
        :return: Callable function
        """

        mock_retailer_params.update(retailer_params)  # type: ignore
        nonlocal mock_retailer
        mock_retailer = RetailerRewards(**mock_retailer_params)
        vela_db_session.add(mock_retailer)
        vela_db_session.commit()

        return mock_retailer

    yield _create_mock_retailer

    vela_db_session.delete(mock_retailer)
    vela_db_session.commit()


@pytest.fixture(scope="function")
def create_mock_reward_rule(vela_db_session: "Session") -> Generator:
    mock_reward_rule: RewardRule = None

    def _create_mock_reward_rule(voucher_type_slug: str, campaign_id: int, reward_goal: int = 5) -> RewardRule:
        """
        Create a reward rule in the test DB
        :return: Callable function
        """
        nonlocal mock_reward_rule
        mock_reward_rule = RewardRule(
            reward_goal=reward_goal, voucher_type_slug=voucher_type_slug, campaign_id=campaign_id
        )
        vela_db_session.add(mock_reward_rule)
        vela_db_session.commit()
        return mock_reward_rule

    yield _create_mock_reward_rule

    vela_db_session.delete(mock_reward_rule)
    vela_db_session.commit()
