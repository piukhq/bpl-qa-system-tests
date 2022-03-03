from sqlalchemy.future import select
from sqlalchemy.orm import Session

from db.polaris.models import AccountHolder, AccountHolderCampaignBalance


def _fetch_balance_for_account_holder(
    polaris_db_session: Session, account_holder: AccountHolder, campaign_slug: str
) -> AccountHolderCampaignBalance:
    account_holder_campaign_balance = (
        polaris_db_session.execute(
            select(AccountHolderCampaignBalance).where(
                AccountHolderCampaignBalance.account_holder_id == account_holder.id,
                AccountHolderCampaignBalance.campaign_slug == campaign_slug,
            )
        )
        .scalars()
        .first()
    )
    return account_holder_campaign_balance
