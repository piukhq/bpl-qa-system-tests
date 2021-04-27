from pytest_bdd import given, scenarios, then, when
from pytest_bdd.parsers import parse

from tests.customer_management_api.api_requests.metrics import get_formatted_metrics
from tests.customer_management_api.response_fixtures.accounts import AccountsResponses
from tests.customer_management_api.response_fixtures.metrics import GenericMetrics
from tests.customer_management_api.step_definitions.shared import enrol_account_holder, enrol_missing_channel_header

scenarios("customer_management_api/metrics/")
accounts_responses = AccountsResponses()


def _get_metric_value(endpoint: str, method: str, status_code: int, retailer_slug: str, metrics: dict) -> float:
    try:
        return metrics[endpoint][retailer_slug][method][str(status_code)]
    except KeyError:
        assert False, "failed to read metrics' value."


@given("I know the current generic metrics' values")
def store_metrics_values(request_context: dict) -> None:
    request_context["metrics"] = get_formatted_metrics()


@when(parse("I make a request to the enrol endpoint for a {retailer_slug} retailer"))
def setup_account_holder_for_metrics(retailer_slug: str, request_context: dict) -> None:
    enrol_account_holder(retailer_slug, request_context)


@when(parse("I make a request to the enrol endpoint for a {retailer_slug} retailer with a missing header"))
def setup_account_holder_for_metrics_no_channel_header(retailer_slug: str, request_context: dict) -> None:
    enrol_missing_channel_header(retailer_slug, request_context)


@then(
    parse(
        "I see the HTTP {status_code} response for the post {retailer_slug}'s enrol" " reflected in the generic metrics"
    )
)
def compare_generic_metrics_after_enrol(status_code: int, retailer_slug: str, request_context: dict) -> None:
    enrol_url = "/bpl/loyalty/[retailer_slug]/accounts/enrolment"
    current_metrics = get_formatted_metrics()

    for metric in GenericMetrics:
        previous_value = _get_metric_value(
            enrol_url, "POST", status_code, retailer_slug, request_context["metrics"][metric.value]
        )
        current_value = _get_metric_value(enrol_url, "POST", status_code, retailer_slug, current_metrics[metric.value])

        assert metric.check_increase(previous_value, current_value)
