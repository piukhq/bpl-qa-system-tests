import logging
import uuid

from typing import TYPE_CHECKING, Any, Generator, Optional

import pytest
from sqlalchemy import delete

from db.carina.session import CarinaSessionMaker
from db.polaris.session import PolarisSessionMaker
from db.vela.session import VelaSessionMaker
from db.carina.models import Voucher, VoucherConfig

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


@pytest.fixture
def create_config_and_vouchers(carina_db_session: "Session") -> Generator:
    voucher_config: Optional[VoucherConfig] = None

    def fn(
        retailer_slug: str, voucher_type_slug: str, status: Optional[str] = "ACTIVE", num_vouchers: int = 5
    ) -> VoucherConfig:
        nonlocal voucher_config
        voucher_config = VoucherConfig(
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
                Voucher(
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
        carina_db_session.execute(delete(Voucher).where(Voucher.voucher_config_id == voucher_config.id))
        carina_db_session.delete(voucher_config)
        carina_db_session.commit()
