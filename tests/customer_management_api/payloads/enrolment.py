import random
from uuid import uuid4

from faker import Faker

from settings import MOCK_SERVICE_BASE_URL

fake = Faker(locale="en_GB")


def all_required_and_all_optional_credentials():
    return {
        "credentials": {
            "email": f"pytest{uuid4()}@bink.com",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "date_of_birth": fake.date_of_birth().strftime("%d/%m/%Y"),
            "phone": str(random.randint(10000000000, 99999999999)),
            "address_line1": fake.secondary_address(),
            "address_line2": fake.street_address(),
            "postcode": fake.postcode(),
            "city": fake.city()
        },
        "marketing_preferences": [],
        # change to a mocked service once one is deployed
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/callback/test-retailer"
    }


def static_request_info():
    return {
        "credentials": {
            "email": f"pytest-static-user@bink.com",
            "first_name": "Robo",
            "last_name": "Bink",
            "date_of_birth": "01/01/1991",
            "phone": 00000000000,
            "address_line1": "1 Fake road",
            "address_line2": "Fake street",
            "postcode": "1FA 1KE",
            "city": "Fake city"
        },
        "marketing_preferences": [],
        # change to a mocked service once one is deployed
        "callback_url": f"{MOCK_SERVICE_BASE_URL}/callback/test-retailer"
    }
