import base64
import hashlib
import hmac
import json
import logging

import httpx
import pytest
import respx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from mcp.server.fastmcp.exceptions import ToolError
from mcp.server.lowlevel.server import request_ctx
from mcp.shared.context import RequestContext
from starlette.requests import Request
from starlette.testclient import TestClient

from conekta_mcp import auth, internal_auth
from conekta_mcp.client import conekta_request
from conekta_mcp.internal_auth import (
    InternalConfig,
    InternalIdentity,
    build_internal_jwt,
    load_internal_config,
    open_company_context,
    seal_company_context,
    set_internal_config,
)
from conekta_mcp.server import mcp
from conekta_mcp.tools import initialize
from conekta_mcp.transports.streamable_http import build_app

TOKEN = "t" * 64
JWT_SECRET = "payments-api-jwt-secret"
INTERNAL_URL = "https://payments-api.internal.test"
CONFIG = InternalConfig(
    token=TOKEN,
    jwt_secret=JWT_SECRET,
    base_url=INTERNAL_URL,
    caller="conekta-payment-agent",
)


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _request(headers=(), state=None) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/mcp",
        "headers": list(headers),
        "query_string": b"",
        "scheme": "https",
        "http_version": "1.1",
        "client": ("127.0.0.1", 1234),
        "server": ("testserver", 443),
    }
    if state is not None:
        scope["state"] = state
    return Request(scope)


def _with_request(request: Request):
    return request_ctx.set(
        RequestContext(
            request_id="req",
            meta=None,
            session=None,
            lifespan_context=None,
            request=request,
        )
    )


def _internal_request(company_id="company_123") -> Request:
    identity = InternalIdentity(company_id=company_id, caller=CONFIG.caller)
    return _request(state={"conekta_internal_identity": identity})


# --- config ---------------------------------------------------------------


def test_config_absent_means_internal_mode_off():
    assert load_internal_config({}) is None


@pytest.mark.parametrize(
    "env",
    [
        {"CONEKTA_MCP_INTERNAL_TOKEN": TOKEN},
        {"PAYMENTS_API_JWT_SECRET": JWT_SECRET},
    ],
)
def test_config_half_configured_refuses_to_start(env):
    with pytest.raises(RuntimeError, match="half-configured"):
        load_internal_config(env)


def test_config_requires_strong_token():
    with pytest.raises(RuntimeError, match="at least 32"):
        load_internal_config(
            {
                "CONEKTA_MCP_INTERNAL_TOKEN": "short",
                "PAYMENTS_API_JWT_SECRET": JWT_SECRET,
                "PAYMENTS_API_INTERNAL_URL": INTERNAL_URL,
            }
        )


def test_config_requires_internal_url():
    with pytest.raises(RuntimeError, match="PAYMENTS_API_INTERNAL_URL"):
        load_internal_config(
            {"CONEKTA_MCP_INTERNAL_TOKEN": TOKEN, "PAYMENTS_API_JWT_SECRET": JWT_SECRET}
        )


def test_config_loads_all_values():
    config = load_internal_config(
        {
            "CONEKTA_MCP_INTERNAL_TOKEN": TOKEN,
            "PAYMENTS_API_JWT_SECRET": JWT_SECRET,
            "PAYMENTS_API_INTERNAL_URL": INTERNAL_URL + "/",
        }
    )

    assert config == CONFIG


# --- JWT and X-Company-Context ------------------------------------------


def test_internal_jwt_is_hs256_with_short_expiration():
    token = build_internal_jwt(JWT_SECRET, "conekta-payment-agent", now=1_000)
    header, payload, signature = token.split(".")

    expected = hmac.new(
        JWT_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256
    ).digest()
    assert _b64decode(signature) == expected
    assert json.loads(_b64decode(header)) == {"alg": "HS256", "typ": "JWT"}
    assert json.loads(_b64decode(payload)) == {
        "iss": "conekta-mcp",
        "sub": "conekta-payment-agent",
        "exp": 1_060,
    }


def test_company_context_matches_payments_api_wire_format():
    value = seal_company_context(JWT_SECRET, "company_123", True, now=1_700_000_000)

    assert "=" not in value
    raw = _b64decode(value)
    iv, sealed = raw[:12], raw[12:]
    # Independent derivation, as payments-api does it:
    # OpenSSL::KDF.hkdf(JWT_SECRET, salt: '', info: KEY_INFO, length: 32, hash: 'SHA256')
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"payments-api/internal-api/company-context",
    ).derive(JWT_SECRET.encode())
    plaintext = AESGCM(key).decrypt(iv, sealed, None)

    assert json.loads(plaintext) == {
        "company_id": "company_123",
        "livemode": True,
        "iat": 1_700_000_000,
    }


def test_company_context_uses_fresh_iv():
    first = seal_company_context(JWT_SECRET, "company_123", True)
    second = seal_company_context(JWT_SECRET, "company_123", True)

    assert first != second
    assert open_company_context(JWT_SECRET, first)["company_id"] == "company_123"


# --- HTTP middleware -----------------------------------------------------


@pytest.fixture
def http_client():
    return TestClient(build_app())


@pytest.mark.parametrize(
    "authorization",
    [None, "Bearer wrong-token", "Bearer key_merchant_private_key", f"Basic {TOKEN}"],
)
def test_company_id_with_invalid_credential_is_401(http_client, authorization):
    set_internal_config(CONFIG)
    headers = {"X-Company-Id": "company_123"}
    if authorization:
        headers["Authorization"] = authorization

    response = http_client.post("/mcp", headers=headers, json={})

    assert response.status_code == 401


def test_company_id_without_internal_config_is_401(http_client):
    response = http_client.post(
        "/mcp",
        headers={"X-Company-Id": "company_123", "Authorization": f"Bearer {TOKEN}"},
        json={},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("company_id", ["", "company 123", "a" * 65, "../x"])
def test_malformed_company_id_is_401(http_client, company_id):
    set_internal_config(CONFIG)

    response = http_client.post(
        "/mcp",
        headers={"X-Company-Id": company_id, "Authorization": f"Bearer {TOKEN}"},
        json={},
    )

    assert response.status_code == 401


def test_valid_internal_request_passes_through(http_client):
    set_internal_config(CONFIG)

    response = http_client.get(
        "/ping",
        headers={"X-Company-Id": "company_123", "Authorization": f"Bearer {TOKEN}"},
    )

    assert response.status_code == 200


def test_public_mode_is_untouched(http_client):
    set_internal_config(CONFIG)

    response = http_client.get("/ping", headers={"Authorization": "Bearer key_xxx"})

    assert response.status_code == 200


def test_authenticate_internal_sets_identity():
    set_internal_config(CONFIG)

    identity = internal_auth.authenticate_internal(f"Bearer {TOKEN}", "company_123")

    assert identity == InternalIdentity("company_123", "conekta-payment-agent")


# --- public mode never forwards the internal credential ------------------


def test_public_mode_rejects_internal_token_without_company():
    set_internal_config(CONFIG)
    auth.set_api_key_provider(auth.get_request_header_api_key)
    token = _with_request(_request([(b"authorization", f"Bearer {TOKEN}".encode())]))

    try:
        with pytest.raises(RuntimeError, match="X-Company-Id"):
            auth.get_api_key()
    finally:
        request_ctx.reset(token)


# --- tool allowlist and payments-api call --------------------------------


@pytest.fixture
def tools_ready():
    initialize()


async def test_internal_mode_lists_only_allowed_tools(tools_ready):
    token = _with_request(_internal_request())
    try:
        tools = await mcp.list_tools()
    finally:
        request_ctx.reset(token)

    assert [tool.name for tool in tools] == ["create_checkout"]


async def test_public_mode_lists_all_tools(tools_ready):
    token = _with_request(_request())
    try:
        tools = await mcp.list_tools()
    finally:
        request_ctx.reset(token)

    assert len(tools) > 1


async def test_internal_mode_rejects_tools_outside_allowlist(tools_ready, caplog):
    token = _with_request(_internal_request())
    try:
        with caplog.at_level(logging.INFO, logger="conekta_mcp.audit"):
            with pytest.raises(ToolError, match="not available in internal mode"):
                await mcp.call_tool("get_balance", {})
    finally:
        request_ctx.reset(token)

    assert "tool=get_balance company_id=company_123" in caplog.text
    assert "allowed=False" in caplog.text


async def test_internal_mode_calls_internal_api_as_company(caplog):
    set_internal_config(CONFIG)
    token = _with_request(_internal_request())
    try:
        with respx.mock() as mock, caplog.at_level(
            logging.INFO, logger="conekta_mcp.audit"
        ):
            route = mock.post(f"{INTERNAL_URL}/internal/api/checkouts").mock(
                return_value=httpx.Response(200, json={"id": "chk_123"})
            )
            result = await conekta_request("POST", "/checkouts", body={"name": "x"})
    finally:
        request_ctx.reset(token)

    assert json.loads(result) == {"id": "chk_123"}
    sent = route.calls[0].request
    scheme, _, jwt = sent.headers["authorization"].partition(" ")
    assert scheme == "Bearer"
    assert jwt.count(".") == 2
    assert TOKEN not in sent.headers["authorization"]
    context = open_company_context(JWT_SECRET, sent.headers["x-company-context"])
    assert context["company_id"] == "company_123"
    assert context["livemode"] is True
    assert (
        "api_call method=POST path=/checkouts company_id=company_123 "
        "caller=conekta-payment-agent status=200"
    ) in caplog.text
