from conekta_mcp.client import conekta_get
from conekta_mcp.server import mcp


@mcp.tool()
async def get_current_company() -> str:
    """Get the current company information associated with the API key."""
    return await conekta_get("/companies/current")
