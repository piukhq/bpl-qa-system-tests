from pytest_bdd import scenarios

# noinspection PyUnresolvedReferences
from tests.shared_utils.shared_steps import *
# noinspection PyUnresolvedReferences
from .step_defs.accounts_steps import *
# noinspection PyUnresolvedReferences
from .step_defs.shared_steps import *

scenarios("./features/accounts/")
