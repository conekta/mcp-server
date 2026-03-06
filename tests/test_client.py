import json

import httpx
import pytest
import respx
from mcp.server.lowlevel.server import request_ctx
from mcp.shared.context import RequestContext
from starlette.requests import Request

from conekta_mcp import auth
from conekta_mcp.client import USER_AGENT, conekta_get, conekta_request, get_client


def _request_with_headers(headers: list[tuple[bytes, bytes]]) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": headers,
            "query_string": b"",
            "scheme": "https",
            "http_version": "1.1",
            "client": ("127.0.0.1", 1234),
            "server": ("testserver", 443),
        }
    )


def test_get_client_sets_default_headers():
    client = get_client()
    assert "conekta" in client.headers["accept"]
    assert "authorization" not in client.headers
    assert client.headers["user-agent"] == USER_AGENT


@pytest.mark.asyncio
async def test_conekta_get_missing_key(monkeypatch):
    monkeypatch.delenv("CONEKTA_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="CONEKTA_API_KEY environment variable"):
        await conekta_get("/balance")


def test_conekta_request_uses_authorization_header_from_request_context():
    auth.set_api_key_provider(auth.get_request_header_api_key)
    request = _request_with_headers([(b"authorization", b"Bearer key_from_header")])
    token = request_ctx.set(
        RequestContext(
            request_id="req_1",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        assert get_client().headers.get("authorization") is None
        assert auth.get_api_key() == "key_from_header"
    finally:
        request_ctx.reset(token)


@pytest.mark.asyncio
async def test_conekta_request_sends_request_authorization_header(mock_api):
    auth.set_api_key_provider(auth.get_request_header_api_key)
    route = mock_api.get("/balance").mock(
        return_value=httpx.Response(200, json={"balance": 1000})
    )
    request = _request_with_headers([(b"authorization", b"Bearer key_from_header")])
    token = request_ctx.set(
        RequestContext(
            request_id="req_2",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        await conekta_get("/balance")
    finally:
        request_ctx.reset(token)

    assert len(route.calls) == 1
    sent_request = route.calls[0].request
    assert sent_request.headers["authorization"] == "Bearer key_from_header"
    assert sent_request.headers["user-agent"] == USER_AGENT


def test_request_header_provider_requires_bearer_format():
    auth.set_api_key_provider(auth.get_request_header_api_key)
    request = _request_with_headers([(b"authorization", b"Basic key_from_header")])
    token = request_ctx.set(
        RequestContext(
            request_id="req_3",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )

    try:
        with pytest.raises(RuntimeError, match="Bearer token format"):
            auth.get_api_key()
    finally:
        request_ctx.reset(token)


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


@pytest.mark.asyncio
async def test_conekta_request_sends_json_body(mock_api):
    """Verify that POST requests actually send the JSON body with correct headers."""
    route = mock_api.post("/checkouts").mock(
        return_value=httpx.Response(201, json={"id": "chk_1"})
    )
    body = {"name": "Test", "type": "PaymentLink", "recurrent": False}
    await conekta_request("POST", "/checkouts", body=body)

    assert len(route.calls) == 1
    request = route.calls[0].request

    # Verify body was actually sent
    sent_body = json.loads(request.content)
    assert sent_body == body

    # Verify Content-Type is application/json (not vendor type)
    assert request.headers["content-type"] == "application/json"
