import json as _json

from conekta_mcp.client import build_params, conekta_get, conekta_request
from conekta_mcp.server import mcp


@mcp.tool()
async def create_order(
    currency: str,
    customer_info_customer_id: str | None = None,
    customer_info_name: str | None = None,
    customer_info_email: str | None = None,
    customer_info_phone: str | None = None,
    line_items_json: str | None = None,
    charges_json: str | None = None,
    shipping_lines_json: str | None = None,
    metadata_json: str | None = None,
) -> str:
    """Create a new order. Provide customer_info_customer_id for an existing
    customer, or name/email/phone for a new one.

    Args:
        currency: ISO currency code (e.g., MXN, USD)
        customer_info_customer_id: Existing Conekta customer ID
        customer_info_name: Customer name (if not using existing customer)
        customer_info_email: Customer email (if not using existing customer)
        customer_info_phone: Customer phone E.164 (if not using existing customer)
        line_items_json: JSON array of line items: [{"name":"Item","unit_price":1000,"quantity":1}]
        charges_json: JSON array of charges: [{"payment_method":{"type":"card","token_id":"tok_..."}}]
        shipping_lines_json: JSON array of shipping lines: [{"amount":500,"carrier":"FedEx"}]
        metadata_json: JSON object of metadata: {"key":"value"}
    """
    body: dict = {"currency": currency}

    if customer_info_customer_id:
        body["customer_info"] = {"customer_id": customer_info_customer_id}
    else:
        ci = build_params(
            name=customer_info_name,
            email=customer_info_email,
            phone=customer_info_phone,
        )
        if ci:
            body["customer_info"] = ci

    for field, value in [
        ("line_items", line_items_json),
        ("charges", charges_json),
        ("shipping_lines", shipping_lines_json),
        ("metadata", metadata_json),
    ]:
        if value:
            try:
                body[field] = _json.loads(value)
            except _json.JSONDecodeError:
                return f'{{"error": true, "message": "Invalid JSON in {field}"}}'

    return await conekta_request("POST", "/orders", body=body)


@mcp.tool()
async def list_orders(
    limit: int = 20,
    search: str | None = None,
    payment_status: str | None = None,
    next_page: str | None = None,
    previous_page: str | None = None,
) -> str:
    """List orders with optional filters and pagination.

    Args:
        limit: Max orders to return (1-250, default 20)
        search: Search by email, reference, etc.
        payment_status: Filter by status (paid, pending, refunded, etc.)
        next_page: Cursor for next page
        previous_page: Cursor for previous page
    """
    params = build_params(
        limit=limit,
        search=search,
        payment_status=payment_status,
        next=next_page,
        previous=previous_page,
    )
    return await conekta_get("/orders", params=params)


@mcp.tool()
async def get_order(order_id: str) -> str:
    """Get order details by ID.

    Args:
        order_id: The Conekta order ID
    """
    return await conekta_get(f"/orders/{order_id}")


@mcp.tool()
async def update_order(
    order_id: str,
    metadata_json: str | None = None,
) -> str:
    """Update an existing order.

    Args:
        order_id: The Conekta order ID
        metadata_json: JSON object of metadata to update: {"key":"value"}
    """
    body: dict = {}
    if metadata_json:
        try:
            body["metadata"] = _json.loads(metadata_json)
        except _json.JSONDecodeError:
            return '{"error": true, "message": "Invalid JSON in metadata"}'
    return await conekta_request("PUT", f"/orders/{order_id}", body=body)


@mcp.tool()
async def cancel_order(order_id: str) -> str:
    """Cancel an order.

    Args:
        order_id: The Conekta order ID to cancel
    """
    return await conekta_request("POST", f"/orders/{order_id}/cancel")


@mcp.tool()
async def capture_order(order_id: str) -> str:
    """Capture a pre-authorized order payment.

    Args:
        order_id: The Conekta order ID to capture
    """
    return await conekta_request("POST", f"/orders/{order_id}/capture")
