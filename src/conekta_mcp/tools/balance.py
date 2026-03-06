from conekta_mcp.client import conekta_get
from conekta_mcp.server import mcp


@mcp.tool()
async def get_balance() -> str:
    """Get the current account balance."""
    return await conekta_get("/balance")
