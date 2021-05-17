import json
import logging
import random

from uuid import uuid4

from faker import Faker

from settings import MOCK_SERVICE_BASE_URL

fake = Faker(locale="en_GB")


def _get_credentials() -> dict:
    phone_prefix = "0" if random.randint(0, 1) else "+44"
    address = fake.street_address().split("\n")
    address_1 = address[0]
    if len(address) > 1:
        address_2 = address[1]
    else:
        address_2 = fake.street_name()

    return {
        "email": f"pytest{uuid4()}@bink.com",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "date_of_birth": fake.date_of_birth().strftime("%Y-%m-%d"),
        "phone": phone_prefix + fake.msisdn(),
        "address_line1": address_1,
        "address_line2": address_2,
        "postcode": fake.postcode(),
        "city": fake.city(),
    }


def all_required_and_all_optional_credentials() -> dict:
    payload = {
        "credentials": _get_credentials(),
        "marketing_preferences": [],
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("`Request body for POST Enrol: " + json.dumps(payload, indent=4))
    return payload


def only_required_credentials() -> dict:
    credentials = _get_credentials()
    del credentials["address_line2"]
    del credentials["postcode"]
    del credentials["city"]
    payload = {
        "credentials": credentials,
        "marketing_preferences": [],
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("`Request body for POST Enrol: " + json.dumps(payload, indent=4))
    return payload


def static_request_info() -> dict:
    payload = {
        "credentials": {
            "email": "pytest-static-account-holder@bink.com",
            "first_name": "Robo",
            "last_name": "Bink",
            "date_of_birth": "1991-01-01",
            "phone": +4400000000000,
            "address_line1": "1 Fake road",
            "address_line2": "Fake street",
            "postcode": "1FA 1KE",
            "city": "Fake city",
        },
        "marketing_preferences": [],
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("`Request body for POST Enrol: " + json.dumps(payload, indent=4))
    return payload


def malformed_request_body() -> str:
    return "malformed request"


def missing_credentials_request_body() -> dict:
    credentials = _get_credentials()
    del credentials["first_name"]
    del credentials["date_of_birth"]
    del credentials["phone"]
    del credentials["address_line1"]

    payload = {
        "credentials": credentials,
        "marketing_preferences": [],
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }

    logging.info("`Request body for missing credentials:  " + json.dumps(payload, indent=4))
    return payload


def bad_field_validation_request_body() -> dict:
    credentials = _get_credentials()
    credentials["email"] = f"pytest{uuid4()}bink.com"
    credentials["date_of_birth"] = "31/12/1990"
    credentials["phone"] = "999"
    credentials["address_line2"] = "road*road"
    credentials["city"] = "city!"

    payload = {
        "credentials": credentials,
        "marketing_preferences": [],
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/enrol/callback/success",
        "third_party_identifier": "identifier",
    }
    logging.info("`Request body for missing validation: " + json.dumps(payload, indent=4))
    return payload
