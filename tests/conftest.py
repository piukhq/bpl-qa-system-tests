import logging
from typing import Any, Generator

import pytest

from db.carina.session import CarinaSessionMaker
from db.polaris.session import PolarisSessionMaker
from db.vela.session import VelaSessionMaker


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
