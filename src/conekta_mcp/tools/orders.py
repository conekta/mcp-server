from conekta_mcp.client import build_params, conekta_get, conekta_request
from conekta_mcp.tools.order_checkout import (
    OrderCheckout,
    validate_checkout,
)
from conekta_mcp.tools.order_charge import OrderCharge
from conekta_mcp.tools.order_line_item import OrderLineItem
from conekta_mcp.tools.metadata import Metadata
from conekta_mcp.tools.order_shipping_contact import OrderShippingContact
from conekta_mcp.tools.order_shipping_line import OrderShippingLine
from conekta_mcp.server import mcp


@mcp.tool()
async def create_order(
    currency: str,
    customer_info_customer_id: str | None = None,
    customer_info_name: str | None = None,
    customer_info_email: str | None = None,
    customer_info_phone: str | None = None,
    checkout: OrderCheckout | None = None,
    line_items: list[OrderLineItem] | None = None,
    charges: list[OrderCharge] | None = None,
    shipping_contact: OrderShippingContact | None = None,
    shipping_lines: list[OrderShippingLine] | None = None,
    metadata: Metadata | None = None,
) -> str:
    """Create a new order. Provide customer_info_customer_id for an existing
    customer, or name/email/phone for a new one.

    Args:
        currency: ISO currency code (e.g., MXN, USD)
        customer_info_customer_id: Existing Conekta customer ID
        customer_info_name: Customer name (if not using existing customer)
        customer_info_email: Customer email (if not using existing customer)
        customer_info_phone: Customer phone E.164 (if not using existing customer)
        checkout: Checkout object. Supported types:
            Integration: {"type":"Integration","allowed_payment_methods":["card"],"name":"Pago"}
            HostedPayment: {"type":"HostedPayment","allowed_payment_methods":["card"],"name":"Pago","success_url":"https://...","failure_url":"https://..."}
        line_items: Order line items: [{"name":"Item","unit_price":1000,"quantity":1}]
        charges: Order charges: [{"payment_method":{"type":"card","token_id":"tok_..."}}]
        shipping_contact: Shipping address: {"address":{"street1":"Nuevo Leon 254","postal_code":"06100","city":"Ciudad de Mexico","state":"Ciudad de Mexico","country":"MX"}}
        shipping_lines: Order shipping lines: [{"amount":500,"carrier":"FedEx"}]
        metadata: Metadata object: {"key":"value"}
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

    if checkout:
        validated_checkout, checkout_error = validate_checkout(checkout)
        if checkout_error:
            return checkout_error
        body["checkout"] = validated_checkout

    if line_items:
        body["line_items"] = line_items

    if charges:
        body["charges"] = charges

    if shipping_contact:
        body["shipping_contact"] = shipping_contact

    if shipping_lines:
        body["shipping_lines"] = shipping_lines

    if metadata:
        body["metadata"] = metadata

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
    metadata: Metadata | None = None,
) -> str:
    """Update an existing order.

    Args:
        order_id: The Conekta order ID
        metadata: Metadata object to update: {"key":"value"}
    """
    body: dict = {}
    if metadata:
        body["metadata"] = metadata
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
