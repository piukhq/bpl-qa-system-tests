from enum import Enum

from retry_tasks_lib.db.models import load_models_to_metadata
from sqlalchemy import MetaData
from sqlalchemy.ext.automap import AutomapBase, automap_base

Base: AutomapBase = automap_base(metadata=MetaData())
load_models_to_metadata(Base.metadata)


class RetailerRewards(Base):
    __tablename__ = "retailer_rewards"


class Campaign(Base):
    __tablename__ = "campaign"


class EarnRule(Base):
    __tablename__ = "earn_rule"


class Transaction(Base):
    __tablename__ = "transaction"


class ProcessedTransaction(Base):
    __tablename__ = "processed_transaction"


class RewardRule(Base):
    __tablename__ = "reward_rule"


class CampaignStatuses(str, Enum):
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    CANCELLED = "CANCELLED"
    ENDED = "ENDED"
