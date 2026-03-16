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
        line_items=[{"name": "Item", "unit_price": 1000, "quantity": 1}],
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
async def test_create_order_with_charges(mock_api):
    route = mock_api.post("/orders").mock(
        return_value=httpx.Response(201, json={"id": "ord_new"})
    )
    await create_order(
        currency="MXN",
        charges=[
            {
                "payment_method": {
                    "type": "card",
                    "token_id": "tok_test",
                }
            }
        ],
    )
    body = json.loads(route.calls[0].request.content)
    assert body["charges"][0]["payment_method"]["type"] == "card"


@pytest.mark.asyncio
async def test_create_order_with_shipping_lines_and_metadata(mock_api):
    route = mock_api.post("/orders").mock(
        return_value=httpx.Response(201, json={"id": "ord_new"})
    )
    await create_order(
        currency="MXN",
        shipping_lines=[{"amount": 500, "carrier": "FedEx"}],
        metadata={"ref": "123"},
    )
    body = json.loads(route.calls[0].request.content)
    assert body["shipping_lines"][0]["amount"] == 500
    assert body["metadata"]["ref"] == "123"


@pytest.mark.asyncio
async def test_create_order_with_integration_checkout(mock_api):
    route = mock_api.post("/orders").mock(
        return_value=httpx.Response(201, json={"id": "ord_new"})
    )
    await create_order(
        currency="MXN",
        checkout={
            "type": "Integration",
            "allowed_payment_methods": ["card", "bank_transfer"],
            "name": "Cobro web",
        },
        line_items=[{"name": "Item", "unit_price": 1000, "quantity": 1}],
    )
    body = json.loads(route.calls[0].request.content)
    assert body["checkout"]["type"] == "Integration"
    assert body["checkout"]["allowed_payment_methods"] == ["card", "bank_transfer"]
    assert body["checkout"]["name"] == "Cobro web"


@pytest.mark.asyncio
async def test_create_order_with_hosted_payment_checkout(mock_api):
    route = mock_api.post("/orders").mock(
        return_value=httpx.Response(201, json={"id": "ord_new"})
    )
    await create_order(
        currency="MXN",
        checkout={
            "type": "HostedPayment",
            "allowed_payment_methods": ["card", "cash"],
            "name": "Pago de Servicio",
            "success_url": "https://example.com/success",
            "failure_url": "https://example.com/failure",
            "redirection_time": 10,
        },
        line_items=[{"name": "Item", "unit_price": 1000, "quantity": 1}],
    )
    body = json.loads(route.calls[0].request.content)
    assert body["checkout"]["type"] == "HostedPayment"
    assert body["checkout"]["success_url"] == "https://example.com/success"
    assert body["checkout"]["failure_url"] == "https://example.com/failure"
    assert body["checkout"]["redirection_time"] == 10


@pytest.mark.asyncio
async def test_create_order_checkout_requires_supported_type():
    result = await create_order(
        currency="MXN",
        checkout={"type": "PaymentLink"},
    )
    data = json.loads(result)
    assert data["error"] is True
    assert "Integration or HostedPayment" in data["message"]


@pytest.mark.asyncio
async def test_create_order_hosted_payment_fields_not_allowed_for_integration():
    result = await create_order(
        currency="MXN",
        checkout={
            "type": "Integration",
            "allowed_payment_methods": ["card"],
            "name": "Pago de Servicio",
            "success_url": "https://example.com/success",
        },
    )
    data = json.loads(result)
    assert data["error"] is True
    assert "HostedPayment" in data["message"]


@pytest.mark.asyncio
async def test_create_order_checkout_requires_object():
    result = await create_order(
        currency="MXN",
        checkout=["HostedPayment"],
    )
    data = json.loads(result)
    assert data["error"] is True
    assert "checkout must be a JSON object" in data["message"]


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
    route = mock_api.put("/orders/ord_1").mock(
        return_value=httpx.Response(200, json={"id": "ord_1"})
    )
    result = await update_order("ord_1", metadata={"ref": "123"})
    data = json.loads(result)
    assert data["id"] == "ord_1"
    body = json.loads(route.calls[0].request.content)
    assert body["metadata"]["ref"] == "123"


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
