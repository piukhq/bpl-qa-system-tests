from retry_tasks_lib.db.models import load_models_to_metadata
from sqlalchemy.ext.automap import AutomapBase, automap_base
from sqlalchemy.orm import relationship

Base: AutomapBase = automap_base()
load_models_to_metadata(Base.metadata)


class AccountHolder(Base):
    __tablename__ = "account_holder"

    retailer = relationship("Retailer", back_populates="account_holders")
    profile = relationship("AccountHolderProfile", uselist=False, back_populates="account_holder")
    pending_rewards = relationship("PendingReward", back_populates="account_holder")
    rewards = relationship("Reward", back_populates="account_holder")
    current_balances = relationship("CampaignBalance", back_populates="account_holder")
    marketing_preferences = relationship("MarketingPreference", back_populates="account_holder")
    transactions = relationship("Transaction", back_populates="account_holder")


class AccountHolderProfile(Base):
    __tablename__ = "account_holder_profile"

    account_holder = relationship("AccountHolder", back_populates="profile")


class MarketingPreference(Base):
    __tablename__ = "marketing_preference"

    account_holder = relationship("AccountHolder", back_populates="marketing_preferences")


class Campaign(Base):
    __tablename__ = "campaign"

    retailer = relationship("Retailer", back_populates="campaigns")
    earn_rule = relationship("EarnRule", cascade="all,delete", back_populates="campaign", uselist=False)
    reward_rule = relationship("RewardRule", cascade="all,delete", back_populates="campaign", uselist=False)
    pending_rewards = relationship("PendingReward", back_populates="campaign")
    current_balances = relationship("CampaignBalance", back_populates="campaign")
    rewards = relationship("Reward", back_populates="campaign")
    # transactions = relationship("Transaction", secondary="transaction_earn", back_populates="campaigns")
    # transaction_earn = relationship("TransactionEarn", back_populates="campaign", overlaps="transactions")


class EarnRule(Base):
    __tablename__ = "earn_rule"

    campaign = relationship("Campaign", back_populates="earn_rule")
    transaction_earns = relationship("TransactionEarn", back_populates="earn_rule")


class RewardRule(Base):
    __tablename__ = "reward_rule"

    campaign = relationship("Campaign", back_populates="reward_rule")
    reward_config = relationship("RewardConfig", back_populates="reward_rules")


class Reward(Base):
    __tablename__ = "reward"

    account_holder = relationship("AccountHolder", back_populates="rewards")
    reward_config = relationship("RewardConfig", back_populates="rewards")
    retailer = relationship("Retailer", back_populates="rewards")
    campaign = relationship("Campaign", back_populates="rewards")
    reward_updates = relationship("RewardUpdate", back_populates="reward")


class RewardUpdate(Base):
    __tablename__ = "reward_update"

    reward = relationship("Reward", back_populates="reward_updates")


class RewardFileLog(Base):
    __tablename__ = "reward_file_log"


class PendingReward(Base):
    __tablename__ = "pending_reward"

    account_holder = relationship("AccountHolder", back_populates="pending_rewards")
    campaign = relationship("Campaign", back_populates="pending_rewards")


class RewardConfig(Base):
    __tablename__ = "reward_config"

    rewards = relationship("Reward", back_populates="reward_config")
    retailer = relationship("Retailer", back_populates="reward_configs")
    fetch_type = relationship("FetchType", back_populates="reward_configs")
    reward_rules = relationship("RewardRule", back_populates="reward_config")


class Retailer(Base):
    __tablename__ = "retailer"

    account_holders = relationship("AccountHolder", back_populates="retailer")
    campaigns = relationship(Campaign, back_populates="retailer")
    reward_configs = relationship("RewardConfig", back_populates="retailer")
    transactions = relationship("Transaction", back_populates="retailer")
    stores = relationship("RetailerStore", back_populates="retailer")
    email_templates = relationship("EmailTemplate", back_populates="retailer")
    fetch_types = relationship("FetchType", secondary="retailer_fetch_type", back_populates="retailer")
    rewards = relationship("Reward", back_populates="retailer")


class FetchType(Base):
    __tablename__ = "fetch_type"

    retailer = relationship("Retailer", back_populates="fetch_types", secondary="retailer_fetch_type")
    reward_configs = relationship("RewardConfig", back_populates="fetch_type")
    retailer_fetch_type = relationship("RetailerFetchType", back_populates="fetch_type")


class RetailerFetchType(Base):
    __tablename__ = "retailer_fetch_type"
    fetch_type = relationship("FetchType", back_populates="retailer_fetch_type")


class CampaignBalance(Base):
    __tablename__ = "campaign_balance"

    account_holder = relationship("AccountHolder", back_populates="current_balances")
    campaign = relationship("Campaign", back_populates="current_balances")


class EmailTemplate(Base):
    __tablename__ = "email_template"

    retailer = relationship("Retailer", back_populates="email_templates")

    required_keys = relationship(
        "EmailTemplateKey",
        back_populates="email_templates",
        secondary="email_template_required_key",
    )


class EmailTemplateKey(Base):
    __tablename__ = "email_template_key"

    email_templates = relationship(
        "EmailTemplate",
        back_populates="required_keys",
        secondary="email_template_required_key",
    )


class EmailTemplateRequiredKey(Base):
    __tablename__ = "email_template_required_key"


class RetailerStore(Base):
    __tablename__ = "retailer_store"

    retailer = relationship("Retailer", back_populates="stores")


class Transaction(Base):
    __tablename__ = "transaction"

    account_holder = relationship("AccountHolder", back_populates="transactions")
    retailer = relationship("Retailer", back_populates="transactions")
    # store = relationship(
    #     "RetailerStore",
    #     uselist=False,
    #     primaryjoin="Transaction.mid==RetailerStore.mid",
    #     foreign_keys=Column(String(128), nullable=False, index=True),
    # )
    transaction_earns = relationship("TransactionEarn", back_populates="transaction")


class TransactionEarn(Base):
    __tablename__ = "transaction_earn"

    earn_rule = relationship("EarnRule", uselist=False, back_populates="transaction_earns")
    transaction = relationship("Transaction", uselist=False, back_populates="transaction_earns")
