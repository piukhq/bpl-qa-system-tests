from retry_tasks_lib.db.models import load_models_to_metadata
from sqlalchemy.ext.automap import AutomapBase, automap_base

Base: AutomapBase = automap_base()
load_models_to_metadata(Base.metadata)


class Reward(Base):
    __tablename__ = "reward"


class RewardConfig(Base):
    __tablename__ = "reward_config"


class RewardUpdate(Base):
    __tablename__ = "reward_update"


class RewardFileLog(Base):
    __tablename__ = "reward_file_log"


class FetchType(Base):
    __tablename__ = "fetch_type"


class RetailerFetchType(Base):
    __tablename__ = "retailer_fetch_type"


class Retailer(Base):
    __tablename__ = "retailer"
