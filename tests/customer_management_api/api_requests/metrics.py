import logging
import re

from typing import List

import settings
from tests.customer_management_api.response_fixtures.metrics import GenericMetrics

from tests.retry_requests import retry_session

inbound_http_request_total_match = re.compile(
    r'inbound_http_request_total{endpoint="(.+)",method="([A-Z]+)"'
    r',response_code="([0-9]+)",retailer="(.+)?"} ([0-9]+)'
)
request_latency_seconds_sum_match = re.compile(
    r'request_latency_seconds_sum{endpoint="(.+)",method="([A-Z]+)"'
    r',response_code="([0-9]+)",retailer="(.+)?"} ([0-9.]+)'
)
request_latency_seconds_bucket_match = re.compile(
    r'request_latency_seconds_bucket{endpoint="(.+)",le="\+Inf",method="([A-Z]+)"'
    r',response_code="([0-9]+)",retailer="(.+)?"} ([0-9]+)'
)


def get_metrics() -> str:
    url = f"{settings.POLARIS_URL}:9100/metrics"
    session = retry_session()
    logging.info(f"GET metrics URL is :{url}")
    resp = session.get(url)
    resp.raise_for_status()
    return resp.text


def _counter_metrics_formatter(matched_metrics: List[tuple]) -> dict:
    formatted_metric: dict = {}
    for endpoint, method, response_code, retailer, count in matched_metrics:
        retailer = retailer or "none"

        if endpoint not in formatted_metric:
            formatted_metric[endpoint] = {}

        if retailer not in formatted_metric[endpoint]:
            formatted_metric[endpoint][retailer] = {}

        if method not in formatted_metric[endpoint][retailer]:
            formatted_metric[endpoint][retailer][method] = {}

        formatted_metric[endpoint][retailer][method][response_code] = float(count)

    return formatted_metric


def get_formatted_metrics() -> dict:
    raw_metrics = get_metrics()
    parsed_metrics: dict = {
        GenericMetrics.REQUESTS_COUNTER.value: _counter_metrics_formatter(
            inbound_http_request_total_match.findall(raw_metrics),
        ),
        GenericMetrics.REQUESTS_LATENCY_TOT.value: _counter_metrics_formatter(
            request_latency_seconds_sum_match.findall(raw_metrics)
        ),
        GenericMetrics.REQUESTS_LATENCY_BUCKET.value: _counter_metrics_formatter(
            request_latency_seconds_bucket_match.findall(raw_metrics)
        ),
    }

    return parsed_metrics
