from enum import Enum


class GenericMetrics(Enum):
    REQUESTS_COUNTER = "inbound_http_request_total"
    REQUESTS_LATENCY_TOT = "request_latency_seconds_sum"
    REQUESTS_LATENCY_BUCKET = "request_latency_seconds_bucket"

    def check_increase(self, previous: float, current: float) -> bool:
        if self == self.REQUESTS_LATENCY_TOT:
            return current > previous
        else:
            return current == previous + 1
