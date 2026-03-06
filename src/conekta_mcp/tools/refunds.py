from conekta_mcp.client import conekta_request
from conekta_mcp.server import mcp


@mcp.tool()
async def create_refund(
    order_id: str,
    amount: int,
    reason: str,
) -> str:
    """Create a refund for an order.

    Args:
        order_id: The Conekta order ID to refund
        amount: Refund amount in cents
        reason: Reason for the refund
    """
    body = {"amount": amount, "reason": reason}
    return await conekta_request("POST", f"/orders/{order_id}/refunds", body=body)
