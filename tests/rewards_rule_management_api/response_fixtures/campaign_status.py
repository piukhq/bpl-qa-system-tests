from tests.shared_utils.response_fixtures.base import BaseResponses

INVALID_CONTENT = {
    "display_message": "BPL Schema not matched.",
    "error": "INVALID_CONTENT",
}
INCOMPLETE_STATUS_UPDATE = {
    "display_message": "Not all campaigns were updated as requested.",
    "error": "INCOMPLETE_STATUS_UPDATE",
}
MISSING_CAMPAIGN_COMPONENTS = {
    "display_message": "the provided campaign(s) could not be made active",
    "error": "MISSING_CAMPAIGN_COMPONENTS",
}


class CampaignStatusResponses(BaseResponses):
    invalid_content = INVALID_CONTENT
    incomplete_status_update = INCOMPLETE_STATUS_UPDATE
    missing_campaign_components = MISSING_CAMPAIGN_COMPONENTS

    def __init__(self, errors_with_slugs: tuple[tuple[str, list[str]]]) -> None:
        self.mixed_errors = [
            {"campaigns": campaign_slugs, **self.get_json(error)} for error, campaign_slugs in errors_with_slugs
        ]
