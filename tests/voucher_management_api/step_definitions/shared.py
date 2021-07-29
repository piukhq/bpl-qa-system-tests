import logging


def check_response_status_code(status_code: int, request_context: dict, endpoint: str) -> None:
    resp = request_context["response"]
    logging.info(f"POST {endpoint} response HTTP status code: {resp.status_code}")
    assert resp.status_code == status_code
