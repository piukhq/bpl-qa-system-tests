from retry_tasks_lib.db.models import load_models_to_metadata
from sqlalchemy import text
from sqlalchemy.ext.automap import AutomapBase, automap_base

Base: AutomapBase = automap_base()
load_models_to_metadata(Base.metadata)

utc_timestamp_sql = text("TIMEZONE('utc', CURRENT_TIMESTAMP)")


class AccountHolder(Base):
    __tablename__ = "account_holder"


class AccountHolderProfile(Base):
    __tablename__ = "account_holder_profile"


class AccountHolderReward(Base):
    __tablename__ = "account_holder_reward"


class AccountHolderCampaignBalance(Base):
    __tablename__ = "account_holder_campaign_balance"


class RetailerConfig(Base):
    __tablename__ = "retailer_config"


class RetryTask(Base):
    __tablename__ = "retry_task"
