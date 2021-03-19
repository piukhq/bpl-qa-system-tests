import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def retry_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        allowed_methods=False,
        status_forcelist=[501, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
