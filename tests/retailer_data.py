from datetime import datetime, timezone

RETAILER_DATA = {
    "trenette": {
        "name": "Trenette",
        "account_number_prefix": "TRNT",
        "loyalty_name": "Trenette",
        "profile_config": """
email:
  required: true
  label: email
first_name:
  required: true
  label: first_name
last_name:
  required: true
  label: last_name
""",
        "marketing_preference_config": """
marketing_pref:
  label: Would you like to receive marketing?
  type: boolean
""",
        "default_campaigns": [
            {
                "campaign": {
                    "slug": "campaign_a",
                    "name": "test campaign",
                    "status": "ACTIVE",
                    "earn_inc_is_tx_value": True,
                    "start_date": datetime.now(tz=timezone.utc),
                    "end_date": None,
                },
                "earn_rules": [],
                "reward_goals": [],
            }
        ],
    }
}
