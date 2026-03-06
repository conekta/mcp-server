import json

import httpx
import pytest

from conekta_mcp.tools.events import get_event, list_events


@pytest.mark.asyncio
async def test_list_events(mock_api):
    mock_api.get("/events").mock(
        return_value=httpx.Response(
            200, json={"has_more": False, "data": [{"id": "evt_1"}]}
        )
    )
    result = await list_events()
    data = json.loads(result)
    assert data["data"][0]["id"] == "evt_1"


@pytest.mark.asyncio
async def test_get_event(mock_api):
    mock_api.get("/events/evt_1").mock(
        return_value=httpx.Response(200, json={"id": "evt_1", "type": "charge.paid"})
    )
    result = await get_event("evt_1")
    data = json.loads(result)
    assert data["type"] == "charge.paid"
