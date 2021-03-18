import random
from uuid import uuid4

from faker import Faker

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
        "callback_url": "http://localhost:8081"
    }
