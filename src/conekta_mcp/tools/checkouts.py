import json as _json

from conekta_mcp.client import build_params, conekta_get, conekta_request
from conekta_mcp.server import mcp


@mcp.tool()
async def create_checkout(
    name: str,
    type: str,
    order_template_currency: str,
    order_template_line_items_json: str,
    recurrent: bool = False,
    expires_at: int | None = None,
    allowed_payment_methods_json: str | None = None,
    monthly_installments_enabled: bool = False,
    monthly_installments_options_json: str | None = None,
) -> str:
    """Create a payment link (checkout).

    Args:
        name: Checkout name for identification
        type: Checkout type (PaymentLink or Integration)
        order_template_currency: ISO currency code (e.g., MXN)
        order_template_line_items_json: JSON array: [{"name":"Item","unit_price":1000,"quantity":1}]
        recurrent: Whether this is a recurring payment link
        expires_at: Expiration Unix timestamp (optional)
        allowed_payment_methods_json: JSON array of allowed methods: ["card","cash","bank_transfer"]
        monthly_installments_enabled: Enable monthly installments
        monthly_installments_options_json: JSON array of installment options: [3,6,9,12]
    """
    try:
        line_items = _json.loads(order_template_line_items_json)
    except _json.JSONDecodeError:
        return '{"error": true, "message": "Invalid JSON in order_template_line_items_json"}'

    body: dict = {
        "name": name,
        "type": type,
        "recurrent": recurrent,
        "order_template": {
            "currency": order_template_currency,
            "line_items": line_items,
        },
    }

    if expires_at is not None:
        body["expires_at"] = expires_at

    if allowed_payment_methods_json:
        try:
            body["allowed_payment_methods"] = _json.loads(allowed_payment_methods_json)
        except _json.JSONDecodeError:
            return '{"error": true, "message": "Invalid JSON in allowed_payment_methods_json"}'

    if monthly_installments_enabled:
        body["monthly_installments_enabled"] = True
        if monthly_installments_options_json:
            try:
                body["monthly_installments_options"] = _json.loads(
                    monthly_installments_options_json
                )
            except _json.JSONDecodeError:
                return '{"error": true, "message": "Invalid JSON in monthly_installments_options_json"}'

    return await conekta_request("POST", "/checkouts", body=body)


@mcp.tool()
async def list_checkouts(
    limit: int = 20,
    search: str | None = None,
    next_page: str | None = None,
    previous_page: str | None = None,
) -> str:
    """List payment links (checkouts) with optional search and pagination.

    Args:
        limit: Max checkouts to return (1-250, default 20)
        search: Search filter
        next_page: Cursor for next page
        previous_page: Cursor for previous page
    """
    params = build_params(
        limit=limit, search=search, next=next_page, previous=previous_page
    )
    return await conekta_get("/checkouts", params=params)


@mcp.tool()
async def get_checkout(checkout_id: str) -> str:
    """Get a payment link (checkout) by ID.

    Args:
        checkout_id: The Conekta checkout ID
    """
    return await conekta_get(f"/checkouts/{checkout_id}")


@mcp.tool()
async def cancel_checkout(checkout_id: str) -> str:
    """Cancel a payment link (checkout).

    Args:
        checkout_id: The Conekta checkout ID to cancel
    """
    return await conekta_request("POST", f"/checkouts/{checkout_id}/cancel")


@mcp.tool()
async def send_checkout_email(checkout_id: str, email: str) -> str:
    """Send a payment link via email.

    Args:
        checkout_id: The Conekta checkout ID
        email: Recipient email address
    """
    body = {"email": email}
    return await conekta_request(
        "POST", f"/checkouts/{checkout_id}/email", body=body
    )


@mcp.tool()
async def send_checkout_sms(checkout_id: str, phone: str) -> str:
    """Send a payment link via SMS.

    Args:
        checkout_id: The Conekta checkout ID
        phone: Recipient phone number in E.164 format
    """
    body = {"phone": phone}
    return await conekta_request(
        "POST", f"/checkouts/{checkout_id}/sms", body=body
    )
