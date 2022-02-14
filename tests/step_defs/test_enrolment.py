from pytest_bdd import scenarios, then

from db.carina.models import RewardConfig
from db.polaris.models import RetailerConfig
from db.vela.models import Campaign

scenarios("../features")


@then("Retailer, Campaigns, and RewardConfigs are successfully created in the database")
def enrolment(
    retailer_config: RetailerConfig, standard_campaigns: list[Campaign], standard_reward_configs: list[RewardConfig]
) -> None:
    assert retailer_config is not None
    assert standard_campaigns
    assert standard_reward_configs
