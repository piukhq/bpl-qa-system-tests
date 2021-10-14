from tests.shared_utils.response_fixtures.base import BaseResponses

INVALID_CONTENT = {
    "display_message": "BPL Schema not matched.",
    "error": "INVALID_CONTENT",
}


class CampaignStatusResponses(BaseResponses):
    invalid_content = INVALID_CONTENT
