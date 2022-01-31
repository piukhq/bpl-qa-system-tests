from pytest_bdd import scenarios

from tests.shared_utils.shared_steps import *  # noqa

from .step_defs.active_campaign_slugs_steps import *  # noqa

scenarios("./features/active_campaign_slugs")
