import json

import httpx
import pytest

from conekta_mcp.tools.balance import get_balance


@pytest.mark.asyncio
async def test_get_balance(mock_api):
    mock_api.get("/balance").mock(
        return_value=httpx.Response(
            200, json={"balance": 50000, "currency": "MXN"}
        )
    )
    result = await get_balance()
    data = json.loads(result)
    assert data["balance"] == 50000


@pytest.mark.asyncio
async def test_get_balance_error(mock_api):
    mock_api.get("/balance").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    result = await get_balance()
    data = json.loads(result)
    assert data["error"] is True
