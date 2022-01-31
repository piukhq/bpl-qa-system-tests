from pytest_bdd import scenarios

from tests.shared_utils.shared_steps import *  # noqa

from .step_defs.rewards_status_steps import *  # noqa
from .step_defs.shared_steps import *  # noqa

scenarios("./features/rewards_status")
