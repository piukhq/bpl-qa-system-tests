from pytest_bdd import scenarios

# noinspection PyUnresolvedReferences
from tests.shared_utils.shared_steps import *  # noqa

# noinspection PyUnresolvedReferences
from .step_defs.reward_goal_met_voucher_allocation_steps import *  # noqa

scenarios("./features")
