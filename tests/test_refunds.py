import json

import httpx
import pytest

from conekta_mcp.tools.refunds import create_refund


@pytest.mark.asyncio
async def test_create_refund(mock_api):
    mock_api.post("/orders/ord_1/refunds").mock(
        return_value=httpx.Response(
            201, json={"id": "ref_1", "amount": 5000}
        )
    )
    result = await create_refund("ord_1", amount=5000, reason="customer request")
    data = json.loads(result)
    assert data["id"] == "ref_1"
    assert data["amount"] == 5000


@pytest.mark.asyncio
async def test_create_refund_error(mock_api):
    mock_api.post("/orders/ord_1/refunds").mock(
        return_value=httpx.Response(
            422, json={"details": [{"message": "amount exceeds charge"}]}
        )
    )
    result = await create_refund("ord_1", amount=999999, reason="test")
    data = json.loads(result)
    assert data["error"] is True
