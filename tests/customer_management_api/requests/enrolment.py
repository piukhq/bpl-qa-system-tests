import json

import requests

from tests.customer_management_api.requests.base import get_url, Endpoints, get_headers


def send_post_enrolment(retailer, request_body):
    url = get_url(retailer, Endpoints.ENROL)
    headers = get_headers()
    return requests.post(url, headers=headers, data=json.dumps(request_body))
