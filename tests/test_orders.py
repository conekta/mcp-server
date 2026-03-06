import json

import httpx
import pytest

from conekta_mcp.tools.orders import (
    cancel_order,
    capture_order,
    create_order,
    get_order,
    list_orders,
    update_order,
)


@pytest.mark.asyncio
async def test_list_orders(mock_api):
    mock_api.get("/orders").mock(
        return_value=httpx.Response(
            200, json={"has_more": False, "data": [{"id": "ord_1"}]}
        )
    )
    result = await list_orders()
    data = json.loads(result)
    assert data["data"][0]["id"] == "ord_1"


@pytest.mark.asyncio
async def test_list_orders_with_payment_status(mock_api):
    route = mock_api.get("/orders").mock(
        return_value=httpx.Response(200, json={"has_more": False, "data": []})
    )
    await list_orders(payment_status="paid")
    assert route.calls[0].request.url.params["payment_status"] == "paid"


@pytest.mark.asyncio
async def test_create_order_with_customer_id(mock_api):
    mock_api.post("/orders").mock(
        return_value=httpx.Response(201, json={"id": "ord_new"})
    )
    result = await create_order(
        currency="MXN",
        customer_info_customer_id="cus_1",
        line_items_json='[{"name":"Item","unit_price":1000,"quantity":1}]',
    )
    data = json.loads(result)
    assert data["id"] == "ord_new"


@pytest.mark.asyncio
async def test_create_order_with_new_customer(mock_api):
    route = mock_api.post("/orders").mock(
        return_value=httpx.Response(201, json={"id": "ord_new"})
    )
    await create_order(
        currency="MXN",
        customer_info_name="Bob",
        customer_info_email="bob@test.com",
        customer_info_phone="+521555",
    )
    body = json.loads(route.calls[0].request.content)
    assert body["customer_info"]["name"] == "Bob"


@pytest.mark.asyncio
async def test_create_order_invalid_json():
    result = await create_order(currency="MXN", line_items_json="not json")
    data = json.loads(result)
    assert data["error"] is True
    assert "line_items" in data["message"]


@pytest.mark.asyncio
async def test_get_order(mock_api):
    mock_api.get("/orders/ord_1").mock(
        return_value=httpx.Response(200, json={"id": "ord_1"})
    )
    result = await get_order("ord_1")
    data = json.loads(result)
    assert data["id"] == "ord_1"


@pytest.mark.asyncio
async def test_update_order(mock_api):
    mock_api.put("/orders/ord_1").mock(
        return_value=httpx.Response(200, json={"id": "ord_1"})
    )
    result = await update_order("ord_1", metadata_json='{"ref":"123"}')
    data = json.loads(result)
    assert data["id"] == "ord_1"


@pytest.mark.asyncio
async def test_cancel_order(mock_api):
    mock_api.post("/orders/ord_1/cancel").mock(
        return_value=httpx.Response(200, json={"id": "ord_1", "status": "cancelled"})
    )
    result = await cancel_order("ord_1")
    data = json.loads(result)
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_capture_order(mock_api):
    mock_api.post("/orders/ord_1/capture").mock(
        return_value=httpx.Response(200, json={"id": "ord_1", "status": "paid"})
    )
    result = await capture_order("ord_1")
    data = json.loads(result)
    assert data["status"] == "paid"
