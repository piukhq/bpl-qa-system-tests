import logging

import pytest


# Hooks
def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """This function will log the failed BDD-Step at the end of logs"""
    logging.info(f"Step failed: {step}")


def pytest_html_report_title(report):
    """Customized title for html report"""
    report.title = "BPL Test Automation Results"


@pytest.fixture(scope='function')
def request_context():
    return {}
