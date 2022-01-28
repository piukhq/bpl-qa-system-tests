import uuid

from sqlalchemy import Boolean, Column, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.automap import automap_base

from db.polaris.session import engine

Base = automap_base()
utc_timestamp_sql = text("TIMEZONE('utc', CURRENT_TIMESTAMP)")


class AccountHolder(Base):  # type: ignore
    __tablename__ = "account_holder"

    account_holder_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=utc_timestamp_sql, nullable=False)
    updated_at = Column(DateTime, server_default=utc_timestamp_sql, onupdate=utc_timestamp_sql, nullable=False)


Base.prepare(engine, reflect=True)

# get models from Base mapping
AccountHolderProfile = Base.classes.account_holder_profile
AccountHolderReward = Base.classes.account_holder_reward
AccountHolderCampaignBalance = Base.classes.account_holder_campaign_balance
RetailerConfig = Base.classes.retailer_config
