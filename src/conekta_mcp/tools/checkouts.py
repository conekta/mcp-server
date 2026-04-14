from conekta_mcp.client import build_params, conekta_get, conekta_request
from conekta_mcp.server import mcp
from conekta_mcp.tools.order_checkout import invalid_json_error, parse_json_field

PAYMENT_LINK_TYPE = "PaymentLink"


def _build_line_items(
    line_items_json: str | None,
    item_name: str,
    item_unit_price: int,
) -> tuple[list, str | None]:
    if line_items_json:
        items, err = parse_json_field("line_items_json", line_items_json)
        if err:
            return [], err
        return items, None
    return [{"name": item_name, "unit_price": item_unit_price, "quantity": 1}], None


def _build_customer_info(customer_info_json: str | None) -> tuple[dict | None, str | None]:
    if not customer_info_json:
        return None, None
    return parse_json_field("customer_info_json", customer_info_json)


@mcp.tool()
async def create_checkout(
    name: str,
    recurrent: bool,
    expires_at: int,
    allowed_payment_methods: str,
    order_template_currency: str,
    item_name: str,
    item_unit_price: int,
    customer_info_json: str | None = None,
    line_items_json: str | None = None,
    monthly_installments_options: list[int] | None = None,
    success_url: str | None = None,
    failure_url: str | None = None,
    origin: str | None = None,
) -> str:
    """Create a payment link (checkout).

    Args:
        name: Checkout name for identification
        recurrent: false for single use, true for multiple payments
        expires_at: Expiration Unix timestamp (10 minutes to 365 days from now)
        allowed_payment_methods: Comma-separated payment methods (e.g., "card,cash,bank_transfer")
        order_template_currency: ISO currency code (e.g., MXN)
        item_name: Product name for the single line item (ignored when line_items_json is provided)
        item_unit_price: Price in cents for the single line item (ignored when line_items_json is provided)
        customer_info_json: JSON object with customer info — either {"customer_id": "cus_xxx"} or {"name": "...", "email": "...", "phone": "..."}
        line_items_json: JSON array for multiple items: [{"name":"Item","unit_price":1000,"quantity":2}]
        monthly_installments_options: Enable installments with these options (e.g., [3,6,9,12])
        success_url: Redirect URL after successful payment
        failure_url: Redirect URL after failed payment
        origin: Origin identifier for the checkout (e.g., "PaymentAgentTelegram")
    """
    line_items, err = _build_line_items(line_items_json, item_name, item_unit_price)
    if err:
        return err

    customer_info, err = _build_customer_info(customer_info_json)
    if err:
        return err

    order_template: dict = {"currency": order_template_currency, "line_items": line_items}
    if customer_info:
        order_template["customer_info"] = customer_info

    body: dict = {
        "name": name,
        "type": PAYMENT_LINK_TYPE,
        "recurrent": recurrent,
        "needs_shipping_contact": False,
        "expires_at": expires_at,
        "allowed_payment_methods": [m.strip() for m in allowed_payment_methods.split(",")],
        "order_template": order_template,
    }

    if monthly_installments_options:
        body["monthly_installments_enabled"] = True
        body["monthly_installments_options"] = monthly_installments_options
    if success_url:
        body["success_url"] = success_url
    if failure_url:
        body["failure_url"] = failure_url
    if origin:
        body["origin"] = origin

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
