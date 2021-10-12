def get_campaign_status_change_payload(request_context: dict) -> dict:
    active_campaigns = request_context["active_campaigns"]

    payload = {
        "requested_status": "Ended",
        "campaign_slugs": [campaign.slug for campaign in active_campaigns],
    }

    return payload


def get_malformed_request_body() -> str:
    return "malformed request"
