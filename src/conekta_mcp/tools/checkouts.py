import json as _json

from conekta_mcp.client import build_params, conekta_get, conekta_request
from conekta_mcp.server import mcp

PAYMENT_LINK_TYPE = "PaymentLink"


@mcp.tool()
async def create_checkout(
    name: str,
    recurrent: bool,
    expires_at: int,
    allowed_payment_methods: str,
    order_template_currency: str,
    item_name: str,
    item_unit_price: int,
    item_quantity: int = 1,
    needs_shipping_contact: bool = False,
    customer_info_customer_id: str | None = None,
    customer_info_name: str | None = None,
    customer_info_email: str | None = None,
    customer_info_phone: str | None = None,
    line_items_json: str | None = None,
    monthly_installments_enabled: bool = False,
    monthly_installments_options: list[int] | None = None,
    success_url: str | None = None,
    failure_url: str | None = None,
) -> str:
    """Create a payment link (checkout).

    Args:
        name: Checkout name for identification
        recurrent: false for single use, true for multiple payments
        expires_at: Expiration Unix timestamp (10 minutes to 365 days from now)
        allowed_payment_methods: Comma-separated payment methods (e.g., "card,cash,bank_transfer")
        order_template_currency: ISO currency code (e.g., MXN)
        item_name: Product name for the line item
        item_unit_price: Price per unit in cents (e.g., 50000 for $500.00 MXN)
        item_quantity: Number of units (default 1)
        needs_shipping_contact: Whether shipping contact info is required (default false)
        customer_info_customer_id: Existing Conekta customer ID (e.g., cus_2tXyF9BwPG14UMkAA)
        customer_info_name: Customer name (if not using existing customer)
        customer_info_email: Customer email (if not using existing customer)
        customer_info_phone: Customer phone E.164 (if not using existing customer)
        line_items_json: JSON array for multiple items, overrides item_name/unit_price/quantity: [{"name":"Item","unit_price":1000,"quantity":1}]
        monthly_installments_enabled: Enable monthly installments
        monthly_installments_options: Installment options (e.g., [3,6,9,12])
        success_url: Redirect URL after successful payment
        failure_url: Redirect URL after failed payment
    """
    methods = [m.strip() for m in allowed_payment_methods.split(",")]

    if line_items_json:
        try:
            line_items = _json.loads(line_items_json)
        except _json.JSONDecodeError:
            return '{"error": true, "message": "Invalid JSON in line_items_json"}'
    else:
        line_items = [
            {"name": item_name, "unit_price": item_unit_price, "quantity": item_quantity}
        ]

    order_template: dict = {
        "currency": order_template_currency,
        "line_items": line_items,
    }

    if customer_info_customer_id:
        order_template["customer_info"] = {"customer_id": customer_info_customer_id}
    elif customer_info_name or customer_info_email or customer_info_phone:
        ci: dict = {}
        if customer_info_name:
            ci["name"] = customer_info_name
        if customer_info_email:
            ci["email"] = customer_info_email
        if customer_info_phone:
            ci["phone"] = customer_info_phone
        order_template["customer_info"] = ci

    body: dict = {
        "name": name,
        "type": PAYMENT_LINK_TYPE,
        "recurrent": recurrent,
        "needs_shipping_contact": needs_shipping_contact,
        "expires_at": expires_at,
        "allowed_payment_methods": methods,
        "order_template": order_template,
    }

    if monthly_installments_enabled:
        body["monthly_installments_enabled"] = True
        if monthly_installments_options:
            body["monthly_installments_options"] = monthly_installments_options

    if success_url:
        body["success_url"] = success_url
    if failure_url:
        body["failure_url"] = failure_url

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
    return await conekta_request("PUT", f"/checkouts/{checkout_id}/cancel")


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
