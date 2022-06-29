from retry_tasks_lib.db.models import load_models_to_metadata
from sqlalchemy.ext.automap import AutomapBase, automap_base
from sqlalchemy.orm import relationship

Base: AutomapBase = automap_base()
load_models_to_metadata(Base.metadata)


class FetchType(Base):
    __tablename__ = "fetch_type"

    retailers = relationship(
        "Retailer",
        back_populates="fetch_types",
        secondary="retailer_fetch_type",
        overlaps="retailerfetchtype_collection",
    )
    retailerfetchtype_collection = relationship("RetailerFetchType", back_populates="fetchtype")


class RetailerFetchType(Base):
    __tablename__ = "retailer_fetch_type"

    retailer = relationship("Retailer", back_populates="retailerfetchtype_collection", overlaps="fetch_types,retailers")
    fetchtype = relationship(
        "FetchType", back_populates="retailerfetchtype_collection", overlaps="fetch_types,retailers"
    )


class Retailer(Base):
    __tablename__ = "retailer"

    fetch_types = relationship(
        "FetchType",
        back_populates="retailers",
        secondary="retailer_fetch_type",
        overlaps="retailerfetchtype_collection",
    )
    retailerfetchtype_collection = relationship("RetailerFetchType", back_populates="retailer", overlaps="fetch_types")


class Reward(Base):
    __tablename__ = "reward"


class RewardConfig(Base):
    __tablename__ = "reward_config"


class RewardUpdate(Base):
    __tablename__ = "reward_update"


class RewardFileLog(Base):
    __tablename__ = "reward_file_log"


class RetryTask(Base):
    __tablename__ = "retry_task"


class TaskType(Base):
    __tablename__ = "task_type"


class TaskTypeKey(Base):
    __tablename__ = "task_type_key"


class TaskTypeKeyValue(Base):
    __tablename__ = "task_type_key_value"
