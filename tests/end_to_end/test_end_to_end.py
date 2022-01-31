from pytest_bdd import scenarios

from tests.shared_utils.shared_steps import *  # noqa

from .step_defs.reward_goal_met_reward_allocation_steps import *  # noqa

scenarios("./features")
