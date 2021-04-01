import json
import logging

from tests.customer_management_api.requests.base import get_url, Endpoints, get_headers, get_invalid_headers
from tests.retry_requests import retry_session


def send_post_enrolment(retailer_slug, request_body):
    url = get_url(retailer_slug, Endpoints.ENROL)
    headers = get_headers()
    session = retry_session()
    logging.info(f"POST enrol URL is :{url}")
    return session.post(url, headers=headers, data=json.dumps(request_body))


def send_malformed_enrolment(retailer_slug, request_body):
    url = get_url(retailer_slug, Endpoints.ENROL)
    headers = get_headers()
    session = retry_session()
    logging.info(f"POST enrol URL is : {url}")
    return session.post(url, headers=headers, data=json.dumps(request_body))


def send_Invalid_post_enrolment(retailer_slug, request_body):
    url = get_url(retailer_slug, Endpoints.ENROL)
    headers = get_invalid_headers()
    session = retry_session()
    logging.info(f"POST enrol URL is :{url}")
    return session.post(url, headers=headers, data=json.dumps(request_body))
