from tests.shared_utils.response_fixtures.base import BaseResponses

INVALID_CONTENT = {
    "display_message": "BPL Schema not matched.",
    "error": "INVALID_CONTENT",
}
INCOMPLETE_STATUS_UPDATE = {
    "display_message": "Not all campaigns were updated as requested.",
    "error": "INCOMPLETE_STATUS_UPDATE",
}


class CampaignStatusResponses(BaseResponses):
    invalid_content = INVALID_CONTENT
    incomplete_status_update = INCOMPLETE_STATUS_UPDATE
