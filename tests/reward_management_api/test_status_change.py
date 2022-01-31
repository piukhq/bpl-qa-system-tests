from pytest_bdd import scenarios

from tests.shared_utils.shared_steps import *  # noqa

from .step_defs.reward_status_change_steps import *  # noqa

scenarios("./features/status_change")
