from conekta_mcp.client import build_params, conekta_get
from conekta_mcp.server import mcp


@mcp.tool()
async def list_events(
    limit: int = 20,
    next_page: str | None = None,
    previous_page: str | None = None,
) -> str:
    """List system events with pagination.

    Args:
        limit: Max events to return (1-250, default 20)
        next_page: Cursor for next page
        previous_page: Cursor for previous page
    """
    params = build_params(
        limit=limit, next=next_page, previous=previous_page
    )
    return await conekta_get("/events", params=params)


@mcp.tool()
async def get_event(event_id: str) -> str:
    """Get an event by ID.

    Args:
        event_id: The Conekta event ID
    """
    return await conekta_get(f"/events/{event_id}")
