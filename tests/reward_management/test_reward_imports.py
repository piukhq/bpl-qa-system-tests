from pytest_bdd import scenarios

from .step_defs.new_reward_imports_steps import *  # noqa

# noinspection PyUnresolvedReferences
from .step_defs.shared_steps import *  # noqa
from .step_defs.reward_update_imports_steps import *  # noqa

scenarios("./features/imports")
