from pytest_bdd import scenarios

from tests.shared_utils.shared_steps import *  # noqa

from .step_defs.campaign_status_steps import *  # noqa

scenarios("./features/campaign_status")
