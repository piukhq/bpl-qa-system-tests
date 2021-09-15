from pytest_bdd import scenarios

# noinspection PyUnresolvedReferences
from .step_defs.new_voucher_imports_steps import *  # noqa
from .step_defs.voucher_update_imports_steps import *  # noqa

scenarios("./features/imports")
