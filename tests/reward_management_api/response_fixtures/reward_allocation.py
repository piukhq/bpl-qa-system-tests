from tests.shared_utils.response_fixtures.base import BaseResponses

UNKNOWN_REWARD_SLUG = {"display_message": "Reward Slug does not exist.", "code": "UNKNOWN_REWARD_SLUG"}


class RewardAllocationResponses(BaseResponses):
    unknown_reward_slug = UNKNOWN_REWARD_SLUG
