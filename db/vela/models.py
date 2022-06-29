from enum import Enum

from retry_tasks_lib.db.models import load_models_to_metadata
from sqlalchemy import MetaData
from sqlalchemy.ext.automap import AutomapBase, automap_base

Base: AutomapBase = automap_base(metadata=MetaData())
load_models_to_metadata(Base.metadata)


class RetailerRewards(Base):
    __tablename__ = "retailer_rewards"


class RetailerStore(Base):
    __tablename__ = "retailer_store"


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


class RetryTask(Base):
    __tablename__ = "retry_task"


class TaskType(Base):
    __tablename__ = "task_type"


class TaskTypeKey(Base):
    __tablename__ = "task_type_key"


class TaskTypeKeyValue(Base):
    __tablename__ = "task_type_key_value"


class CampaignStatuses(str, Enum):
    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    CANCELLED = "CANCELLED"
    ENDED = "ENDED"
