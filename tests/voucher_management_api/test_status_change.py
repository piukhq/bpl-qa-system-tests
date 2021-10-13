from pytest_bdd import scenarios

# noinspection PyUnresolvedReferences
from tests.shared_utils.shared_steps import *  # noqa

# noinspection PyUnresolvedReferences
from .step_defs.voucher_status_change_steps import *  # noqa

scenarios("./features/status_change")
