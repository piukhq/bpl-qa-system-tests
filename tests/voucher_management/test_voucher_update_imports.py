from pytest_bdd import scenarios

# noinspection PyUnresolvedReferences
from .step_defs.voucher_update_imports import *  # noqa

scenarios("./features/imports")
