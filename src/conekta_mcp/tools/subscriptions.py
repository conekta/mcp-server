from conekta_mcp.client import build_params, conekta_get, conekta_request
from conekta_mcp.server import mcp


@mcp.tool()
async def list_subscriptions(
    customer_id: str,
    limit: int = 20,
    next_page: str | None = None,
    previous_page: str | None = None,
) -> str:
    """List subscriptions for a customer.

    Args:
        customer_id: The Conekta customer ID
        limit: Max subscriptions to return (1-250, default 20)
        next_page: Cursor for next page
        previous_page: Cursor for previous page
    """
    params = build_params(
        limit=limit, next=next_page, previous=previous_page
    )
    return await conekta_get(
        f"/customers/{customer_id}/subscriptions", params=params
    )


@mcp.tool()
async def get_subscription(customer_id: str, subscription_id: str) -> str:
    """Get subscription details.

    Args:
        customer_id: The Conekta customer ID
        subscription_id: The subscription ID
    """
    return await conekta_get(
        f"/customers/{customer_id}/subscriptions/{subscription_id}"
    )


@mcp.tool()
async def create_subscription(
    customer_id: str,
    plan_id: str,
    card_id: str | None = None,
) -> str:
    """Create a subscription for a customer.

    Args:
        customer_id: The Conekta customer ID
        plan_id: The plan ID to subscribe to
        card_id: Payment source ID (uses default if not provided)
    """
    body: dict = {"plan_id": plan_id}
    if card_id:
        body["card_id"] = card_id
    return await conekta_request(
        "POST", f"/customers/{customer_id}/subscriptions", body=body
    )


@mcp.tool()
async def update_subscription(
    customer_id: str,
    subscription_id: str,
    plan_id: str | None = None,
    card_id: str | None = None,
) -> str:
    """Update a subscription.

    Args:
        customer_id: The Conekta customer ID
        subscription_id: The subscription ID
        plan_id: New plan ID
        card_id: New payment source ID
    """
    body = build_params(plan_id=plan_id, card_id=card_id)
    if not body:
        return '{"error": true, "message": "No fields provided to update"}'
    return await conekta_request(
        "PUT",
        f"/customers/{customer_id}/subscriptions/{subscription_id}",
        body=body,
    )


@mcp.tool()
async def cancel_subscription(customer_id: str, subscription_id: str) -> str:
    """Cancel a subscription.

    Args:
        customer_id: The Conekta customer ID
        subscription_id: The subscription ID to cancel
    """
    return await conekta_request(
        "POST",
        f"/customers/{customer_id}/subscriptions/{subscription_id}/cancel",
    )


@mcp.tool()
async def pause_subscription(customer_id: str, subscription_id: str) -> str:
    """Pause a subscription.

    Args:
        customer_id: The Conekta customer ID
        subscription_id: The subscription ID to pause
    """
    return await conekta_request(
        "POST",
        f"/customers/{customer_id}/subscriptions/{subscription_id}/pause",
    )


@mcp.tool()
async def resume_subscription(customer_id: str, subscription_id: str) -> str:
    """Resume a paused subscription.

    Args:
        customer_id: The Conekta customer ID
        subscription_id: The subscription ID to resume
    """
    return await conekta_request(
        "POST",
        f"/customers/{customer_id}/subscriptions/{subscription_id}/resume",
    )
