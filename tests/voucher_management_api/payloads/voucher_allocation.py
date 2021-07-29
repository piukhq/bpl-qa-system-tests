from settings import POLARIS_BASE_URL


def get_voucher_allocation_payload(request_context: dict) -> dict:
    account_holder_uuid = request_context["account_holder_uuid"]
    retailer_slug = request_context["retailer"].slug
    account_url = f"{POLARIS_BASE_URL}/{retailer_slug}/accounts/{account_holder_uuid}/vouchers"
    payload = {
        "account_url": account_url,
    }

    return payload


def get_malformed_request_body() -> str:
    return "malformed request"
