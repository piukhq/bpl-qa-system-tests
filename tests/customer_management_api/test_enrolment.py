from pytest_bdd import scenarios

# noinspection PyUnresolvedReferences
from tests.shared_utils.shared_steps import *  # noqa

# noinspection PyUnresolvedReferences
from .step_defs.enrolment_steps import *  # noqa

# noinspection PyUnresolvedReferences
from .step_defs.shared_steps import *  # noqa

scenarios("./features/enrolment")
