import json

import httpx
import pytest

from conekta_mcp.tools.customers import (
    create_customer,
    get_customer,
    list_customers,
    update_customer,
)


@pytest.mark.asyncio
async def test_list_customers(mock_api):
    mock_api.get("/customers").mock(
        return_value=httpx.Response(
            200,
            json={"has_more": False, "data": [{"id": "cus_1", "name": "Alice"}]},
        )
    )
    result = await list_customers()
    data = json.loads(result)
    assert data["data"][0]["id"] == "cus_1"


@pytest.mark.asyncio
async def test_list_customers_with_search(mock_api):
    route = mock_api.get("/customers").mock(
        return_value=httpx.Response(200, json={"has_more": False, "data": []})
    )
    await list_customers(search="alice")
    assert route.calls[0].request.url.params["search"] == "alice"


@pytest.mark.asyncio
async def test_create_customer(mock_api):
    mock_api.post("/customers").mock(
        return_value=httpx.Response(
            201, json={"id": "cus_new", "name": "Bob"}
        )
    )
    result = await create_customer(name="Bob", email="bob@test.com", phone="+521555")
    data = json.loads(result)
    assert data["id"] == "cus_new"


@pytest.mark.asyncio
async def test_create_customer_error(mock_api):
    mock_api.post("/customers").mock(
        return_value=httpx.Response(
            422, json={"details": [{"message": "email is invalid"}]}
        )
    )
    result = await create_customer(name="Bad", email="x", phone="+521555")
    data = json.loads(result)
    assert data["error"] is True
    assert data["status_code"] == 422


@pytest.mark.asyncio
async def test_get_customer(mock_api):
    mock_api.get("/customers/cus_1").mock(
        return_value=httpx.Response(200, json={"id": "cus_1", "name": "Alice"})
    )
    result = await get_customer("cus_1")
    data = json.loads(result)
    assert data["id"] == "cus_1"


@pytest.mark.asyncio
async def test_update_customer(mock_api):
    mock_api.put("/customers/cus_1").mock(
        return_value=httpx.Response(200, json={"id": "cus_1", "name": "Updated"})
    )
    result = await update_customer("cus_1", name="Updated")
    data = json.loads(result)
    assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_update_customer_no_fields():
    result = await update_customer("cus_1")
    data = json.loads(result)
    assert data["error"] is True
