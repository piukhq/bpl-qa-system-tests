from tests.shared_utils.response_fixtures.base import BaseResponses

UNKNOWN_REWARD_TYPE = {"display_message": "Reward Slug does not exist.", "code": "UNKNOWN_REWARD_TYPE"}


class RewardAllocationResponses(BaseResponses):
    unknown_reward_type = UNKNOWN_REWARD_TYPE
