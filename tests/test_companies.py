import json

import httpx
import pytest

from conekta_mcp.tools.companies import get_current_company


@pytest.mark.asyncio
async def test_get_current_company(mock_api):
    mock_api.get("/companies/current").mock(
        return_value=httpx.Response(
            200, json={"id": "comp_1", "name": "Acme Corp"}
        )
    )
    result = await get_current_company()
    data = json.loads(result)
    assert data["name"] == "Acme Corp"
