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
        recurrent=False,
        expires_at=1735689600,
        allowed_payment_methods="card,cash,bank_transfer",
        order_template_currency="MXN",
        item_name="Playera",
        item_unit_price=50000,
        item_quantity=1,
    )
    data = json.loads(result)
    assert data["id"] == "chk_1"


@pytest.mark.asyncio
async def test_create_checkout_with_customer_id(mock_api):
    route = mock_api.post("/checkouts").mock(
        return_value=httpx.Response(201, json={"id": "chk_3"})
    )
    result = await create_checkout(
        name="With Customer",
        recurrent=False,
        expires_at=1735689600,
        allowed_payment_methods="card",
        order_template_currency="MXN",
        item_name="Playera",
        item_unit_price=50000,
        customer_info_customer_id="cus_2tXyF9BwPG14UMkAA",
    )
    data = json.loads(result)
    assert data["id"] == "chk_3"
    sent = json.loads(route.calls[0].request.content)
    assert sent["order_template"]["customer_info"] == {"customer_id": "cus_2tXyF9BwPG14UMkAA"}


@pytest.mark.asyncio
async def test_create_checkout_with_customer_info(mock_api):
    route = mock_api.post("/checkouts").mock(
        return_value=httpx.Response(201, json={"id": "chk_4"})
    )
    result = await create_checkout(
        name="With Info",
        recurrent=False,
        expires_at=1735689600,
        allowed_payment_methods="card",
        order_template_currency="MXN",
        item_name="Playera",
        item_unit_price=50000,
        customer_info_name="Miguel",
        customer_info_email="miguel@test.com",
        customer_info_phone="+5215555555555",
    )
    data = json.loads(result)
    assert data["id"] == "chk_4"
    sent = json.loads(route.calls[0].request.content)
    ci = sent["order_template"]["customer_info"]
    assert ci["name"] == "Miguel"
    assert ci["email"] == "miguel@test.com"


@pytest.mark.asyncio
async def test_create_checkout_with_installments(mock_api):
    route = mock_api.post("/checkouts").mock(
        return_value=httpx.Response(201, json={"id": "chk_5"})
    )
    result = await create_checkout(
        name="Installments",
        recurrent=False,
        expires_at=1735689600,
        allowed_payment_methods="card",
        order_template_currency="MXN",
        item_name="Laptop",
        item_unit_price=2000000,
        monthly_installments_enabled=True,
        monthly_installments_options=[3, 6, 9, 12],
    )
    data = json.loads(result)
    assert data["id"] == "chk_5"
    sent = json.loads(route.calls[0].request.content)
    assert sent["monthly_installments_enabled"] is True
    assert sent["monthly_installments_options"] == [3, 6, 9, 12]


@pytest.mark.asyncio
async def test_create_checkout_with_line_items_json(mock_api):
    mock_api.post("/checkouts").mock(
        return_value=httpx.Response(201, json={"id": "chk_2"})
    )
    result = await create_checkout(
        name="Multi Item",
        recurrent=False,
        expires_at=1735689600,
        allowed_payment_methods="card",
        order_template_currency="MXN",
        item_name="ignored",
        item_unit_price=0,
        line_items_json='[{"name":"A","unit_price":1000,"quantity":1},{"name":"B","unit_price":2000,"quantity":2}]',
    )
    data = json.loads(result)
    assert data["id"] == "chk_2"


@pytest.mark.asyncio
async def test_create_checkout_invalid_json():
    result = await create_checkout(
        name="Bad",
        recurrent=False,
        expires_at=1735689600,
        allowed_payment_methods="card",
        order_template_currency="MXN",
        item_name="X",
        item_unit_price=100,
        line_items_json="not json",
    )
    data = json.loads(result)
    assert data["error"] is True


@pytest.mark.asyncio
async def test_create_checkout_with_origin(mock_api):
    route = mock_api.post("/checkouts").mock(
        return_value=httpx.Response(201, json={"id": "chk_6"})
    )
    result = await create_checkout(
        name="Telegram Checkout",
        recurrent=False,
        expires_at=1735689600,
        allowed_payment_methods="card",
        order_template_currency="MXN",
        item_name="Producto",
        item_unit_price=10000,
        origin="PaymentAgentTelegram",
    )
    data = json.loads(result)
    assert data["id"] == "chk_6"
    sent = json.loads(route.calls[0].request.content)
    assert sent["origin"] == "PaymentAgentTelegram"


@pytest.mark.asyncio
async def test_create_checkout_without_origin(mock_api):
    route = mock_api.post("/checkouts").mock(
        return_value=httpx.Response(201, json={"id": "chk_7"})
    )
    await create_checkout(
        name="No Origin",
        recurrent=False,
        expires_at=1735689600,
        allowed_payment_methods="card",
        order_template_currency="MXN",
        item_name="Producto",
        item_unit_price=10000,
    )
    sent = json.loads(route.calls[0].request.content)
    assert "origin" not in sent


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
    mock_api.put("/checkouts/chk_1/cancel").mock(
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
