from enum import Enum

from sqlalchemy import MetaData
from sqlalchemy.ext.automap import AutomapBase, automap_base

Base: AutomapBase = automap_base(metadata=MetaData())


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
