from pytest_bdd import scenarios

# noinspection PyUnresolvedReferences
from tests.shared_utils.shared_steps import *
# noinspection PyUnresolvedReferences
from .step_defs.active_campaign_slugs_steps import *

scenarios("./features/active_campaign_slugs")
