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


class AccountHolderPendingReward(Base):
    __tablename__ = "account_holder_pending_reward"


class AccountHolderCampaignBalance(Base):
    __tablename__ = "account_holder_campaign_balance"


class AccountHolderMarketingPreference(Base):
    __tablename__ = "account_holder_marketing_preference"


class AccountHolderTransactionHistory(Base):
    __tablename__ = "account_holder_transaction_history"


class BalanceAdjustment(Base):
    __tablename__ = "balance_adjustment"


class EmailTemplate(Base):
    __tablename__ = "email_template"


class EmailTemplateKey(Base):
    __tablename__ = "email_template_key"


class RetailerConfig(Base):
    __tablename__ = "retailer_config"


class RetryTask(Base):
    __tablename__ = "retry_task"


class TaskType(Base):
    __tablename__ = "task_type"


class TaskTypeKey(Base):
    __tablename__ = "task_type_key"


class TaskTypeKeyValue(Base):
    __tablename__ = "task_type_key_value"
