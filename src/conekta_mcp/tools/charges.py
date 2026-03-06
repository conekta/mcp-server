from conekta_mcp.client import build_params, conekta_get
from conekta_mcp.server import mcp


@mcp.tool()
async def list_charges(
    limit: int = 20,
    search: str | None = None,
    next_page: str | None = None,
    previous_page: str | None = None,
) -> str:
    """List all charges with optional search and pagination.

    Args:
        limit: Max charges to return (1-250, default 20)
        search: Search filter
        next_page: Cursor for next page
        previous_page: Cursor for previous page
    """
    params = build_params(
        limit=limit, search=search, next=next_page, previous=previous_page
    )
    return await conekta_get("/charges", params=params)
