from tests.shared.response_fixtures.base import BaseResponses

NO_ACTIVE_CAMPAIGNS = {"display_message": "No active campaigns found for retailer.", "error": "NO_ACTIVE_CAMPAIGNS"}


class ActiveCampaignSlugsResponses(BaseResponses):
    no_active_campaigns = NO_ACTIVE_CAMPAIGNS
