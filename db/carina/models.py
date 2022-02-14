from sqlalchemy import MetaData
from sqlalchemy.ext.automap import AutomapBase, automap_base

Base: AutomapBase = automap_base(metadata=MetaData())


class Reward(Base):
    __tablename__ = "reward"


class RewardConfig(Base):
    __tablename__ = "reward_config"


class RewardUpdate(Base):
    __tablename__ = "reward_update"


class RewardFileLog(Base):
    __tablename__ = "reward_file_log"
