from tests.shared_utils.response_fixtures.base import BaseResponses


class RewardStatusResponses(BaseResponses):
    no_reward_found = {
        "display_message": "Reward not found.",
        "code": "NO_REWARD_FOUND",
    }
    status_not_changed = {
        "display_message": "Reward status incorrect.",
        "code": "STATUS_NOT_CHANGED",
    }
    invalid_status = {
        "display_message": "Status Rejected.",
        "code": "INVALID_STATUS",
    }
    success: dict = {}
