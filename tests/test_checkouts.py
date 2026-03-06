import json

import httpx
import pytest

from conekta_mcp.tools.checkouts import (
    cancel_checkout,
    create_checkout,
    get_checkout,
    list_checkouts,
    send_checkout_email,
    send_checkout_sms,
)


@pytest.mark.asyncio
async def test_create_checkout(mock_api):
    mock_api.post("/checkouts").mock(
        return_value=httpx.Response(201, json={"id": "chk_1", "url": "https://pay.conekta.com/chk_1"})
    )
    result = await create_checkout(
        name="Test Checkout",
        type="PaymentLink",
        order_template_currency="MXN",
        order_template_line_items_json='[{"name":"Item","unit_price":1000,"quantity":1}]',
    )
    data = json.loads(result)
    assert data["id"] == "chk_1"


@pytest.mark.asyncio
async def test_create_checkout_invalid_json():
    result = await create_checkout(
        name="Bad",
        type="PaymentLink",
        order_template_currency="MXN",
        order_template_line_items_json="not json",
    )
    data = json.loads(result)
    assert data["error"] is True


@pytest.mark.asyncio
async def test_list_checkouts(mock_api):
    mock_api.get("/checkouts").mock(
        return_value=httpx.Response(
            200, json={"has_more": False, "data": [{"id": "chk_1"}]}
        )
    )
    result = await list_checkouts()
    data = json.loads(result)
    assert data["data"][0]["id"] == "chk_1"


@pytest.mark.asyncio
async def test_get_checkout(mock_api):
    mock_api.get("/checkouts/chk_1").mock(
        return_value=httpx.Response(200, json={"id": "chk_1"})
    )
    result = await get_checkout("chk_1")
    data = json.loads(result)
    assert data["id"] == "chk_1"


@pytest.mark.asyncio
async def test_cancel_checkout(mock_api):
    mock_api.post("/checkouts/chk_1/cancel").mock(
        return_value=httpx.Response(200, json={"id": "chk_1", "status": "cancelled"})
    )
    result = await cancel_checkout("chk_1")
    data = json.loads(result)
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_send_checkout_email(mock_api):
    mock_api.post("/checkouts/chk_1/email").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await send_checkout_email("chk_1", email="user@test.com")
    data = json.loads(result)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_send_checkout_sms(mock_api):
    mock_api.post("/checkouts/chk_1/sms").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await send_checkout_sms("chk_1", phone="+5215555555555")
    data = json.loads(result)
    assert data["success"] is True
