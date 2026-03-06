import json

import httpx
import pytest

from conekta_mcp.tools.charges import list_charges


@pytest.mark.asyncio
async def test_list_charges(mock_api):
    mock_api.get("/charges").mock(
        return_value=httpx.Response(
            200, json={"has_more": False, "data": [{"id": "chg_1"}]}
        )
    )
    result = await list_charges()
    data = json.loads(result)
    assert data["data"][0]["id"] == "chg_1"
