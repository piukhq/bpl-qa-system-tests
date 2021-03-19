import json

from tests.customer_management_api.requests.base import get_url, Endpoints, get_headers
from tests.retry_requests import retry_session


def send_post_enrolment(retailer_slug, request_body):
    url = get_url(retailer_slug, Endpoints.ENROL)
    headers = get_headers()
    session = retry_session()
    return session.post(url, headers=headers, data=json.dumps(request_body))
