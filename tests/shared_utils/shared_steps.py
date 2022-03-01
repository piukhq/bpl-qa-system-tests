from sqlalchemy.future import select
from sqlalchemy.orm import Session

from db.polaris.models import AccountHolder, AccountHolderCampaignBalance


def _fetch_balance_for_account_holder(
    polaris_db_session: Session, account_holder: AccountHolder, campaign_slug: str
) -> AccountHolderCampaignBalance:
    balance = (
        polaris_db_session.execute(
            select(AccountHolderCampaignBalance).where(
                AccountHolderCampaignBalance.account_holder_id == account_holder.id,
                AccountHolderCampaignBalance.campaign_slug == campaign_slug,
            )
        )
        .scalars()
        .first()
    )
    return balance.balance


# @given(parsers.parse("A {status} account holder exists for {retailer_slug}"))
# def setup_account_holder(status: str, retailer_slug: str, request_context: dict, polaris_db_session: "Session") -> None:
#     email = request_context["email"]
#     retailer = polaris_db_session.query(RetailerConfig).filter_by(slug=retailer_slug).first()
#     if retailer is None:
#         raise ValueError(f"a retailer with slug '{retailer_slug}' was not found in the db.")
#
#     account_status = {"active": "ACTIVE"}.get(status, "PENDING")
#     if "campaign" in request_context:
#         campaign_slug = request_context["campaign"].slug
#     else:
#         campaign_slug = "test-campaign-1"
#
#     account_holder = (
#         polaris_db_session.execute(
#             select(AccountHolder).where(AccountHolder.email == email, AccountHolder.retailer_id == retailer.id)
#         )
#         .scalars()
#         .first()
#     )
#     if account_holder is None:
#
#         account_holder = AccountHolder(
#             email=email,
#             retailer_id=retailer.id,
#             status=account_status,
#         )
#         polaris_db_session.add(account_holder)
#         polaris_db_session.flush()
#
#     else:
#         account_holder.status = account_status
#
#     balance = _setup_balance_for_account_holder(polaris_db_session, account_holder, campaign_slug)
#     polaris_db_session.commit()
#
#     request_context["account_holder_uuid"] = str(account_holder.account_holder_uuid)
#     request_context["account_holder"] = account_holder
#     request_context["retailer_id"] = retailer.id
#     request_context["retailer_slug"] = retailer.slug
#     request_context["start_balance"] = 0
#     request_context["balance"] = balance
#
#     logging.info(f"Active account holder uuid:{account_holder.account_holder_uuid}\n" f"Retailer slug: {retailer_slug}")
