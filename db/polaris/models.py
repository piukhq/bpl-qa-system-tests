import uuid

from sqlalchemy import Boolean, Column, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.automap import AutomapBase, automap_base

Base: AutomapBase = automap_base()
utc_timestamp_sql = text("TIMEZONE('utc', CURRENT_TIMESTAMP)")


class AccountHolder(Base):
    __tablename__ = "account_holder"

    account_holder_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=utc_timestamp_sql, nullable=False)
    updated_at = Column(DateTime, server_default=utc_timestamp_sql, onupdate=utc_timestamp_sql, nullable=False)


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
