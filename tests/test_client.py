import json

import httpx
import pytest
import respx

from conekta_mcp.client import conekta_get, conekta_request, get_client


def test_get_client_sets_auth_header():
    client = get_client()
    assert client.headers["authorization"] == "Bearer test_key_abc123"
    assert "conekta" in client.headers["content-type"]


def test_get_client_missing_key(monkeypatch):
    monkeypatch.delenv("CONEKTA_API_KEY", raising=False)
    from conekta_mcp import client

    client._client = None
    with pytest.raises(RuntimeError, match="CONEKTA_API_KEY"):
        get_client()


@pytest.mark.asyncio
async def test_conekta_get_success(mock_api):
    mock_api.get("/balance").mock(
        return_value=httpx.Response(200, json={"balance": 1000})
    )
    result = await conekta_get("/balance")
    data = json.loads(result)
    assert data["balance"] == 1000


@pytest.mark.asyncio
async def test_conekta_get_http_error(mock_api):
    mock_api.get("/balance").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    result = await conekta_get("/balance")
    data = json.loads(result)
    assert data["error"] is True
    assert data["status_code"] == 401


@pytest.mark.asyncio
async def test_conekta_request_post_success(mock_api):
    mock_api.post("/customers").mock(
        return_value=httpx.Response(201, json={"id": "cus_123"})
    )
    result = await conekta_request("POST", "/customers", body={"name": "Test"})
    data = json.loads(result)
    assert data["id"] == "cus_123"


@pytest.mark.asyncio
async def test_conekta_request_422_error(mock_api):
    mock_api.post("/customers").mock(
        return_value=httpx.Response(
            422, json={"details": [{"message": "email is invalid"}]}
        )
    )
    result = await conekta_request("POST", "/customers", body={"name": "Bad"})
    data = json.loads(result)
    assert data["error"] is True
    assert data["status_code"] == 422


@pytest.mark.asyncio
async def test_conekta_request_204_no_content(mock_api):
    mock_api.post("/orders/ord_1/cancel").mock(
        return_value=httpx.Response(204)
    )
    result = await conekta_request("POST", "/orders/ord_1/cancel")
    data = json.loads(result)
    assert data["success"] is True
