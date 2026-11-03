import pytest

from conekta_mcp import auth
from conekta_mcp.transports import TRANSPORT_RUNNERS
from conekta_mcp.transports import stdio, streamable_http


def test_transport_runners_register_known_transports():
    assert TRANSPORT_RUNNERS == {
        "stdio": stdio.run,
        "streamable-http": streamable_http.run,
    }


def test_stdio_run_sets_env_provider_and_uses_stdio_transport(monkeypatch):
    calls = {}

    def fake_initialize():
        calls["initialized"] = True

    def fake_set_api_key_provider(provider):
        calls["provider"] = provider

    def fake_run(*, transport):
        calls["transport"] = transport

    monkeypatch.setattr(stdio, "initialize", fake_initialize)
    monkeypatch.setattr(stdio, "set_api_key_provider", fake_set_api_key_provider)
    monkeypatch.setattr(stdio.mcp, "run", fake_run)

    stdio.run()

    assert calls == {
        "initialized": True,
        "provider": auth.get_env_api_key,
        "transport": "stdio",
    }


def test_streamable_http_run_sets_header_provider_and_serves_app(monkeypatch):
    calls = {}

    def fake_initialize():
        calls["initialized"] = True

    def fake_set_api_key_provider(provider):
        calls["provider"] = provider

    class FakeServer:
        def __init__(self, config):
            calls["app"] = config.app

        def run(self):
            calls["served"] = True

    monkeypatch.setattr(streamable_http, "initialize", fake_initialize)
    monkeypatch.setattr(
        streamable_http, "set_api_key_provider", fake_set_api_key_provider
    )
    monkeypatch.setattr(streamable_http, "build_app", lambda: "app")
    monkeypatch.setattr(streamable_http.uvicorn, "Server", FakeServer)
    monkeypatch.delenv("CONEKTA_MCP_INTERNAL_TOKEN", raising=False)
    monkeypatch.delenv("PAYMENTS_API_JWT_SECRET", raising=False)

    streamable_http.run()

    assert calls == {
        "initialized": True,
        "provider": auth.get_request_header_api_key,
        "app": "app",
        "served": True,
    }


def test_streamable_http_run_refuses_half_configured_internal_mode(monkeypatch):
    monkeypatch.setattr(streamable_http, "initialize", lambda: None)
    monkeypatch.setattr(streamable_http, "set_api_key_provider", lambda _: None)
    monkeypatch.setattr(
        streamable_http.uvicorn, "Server", lambda _: pytest.fail("must not serve")
    )
    monkeypatch.setenv("CONEKTA_MCP_INTERNAL_TOKEN", "x" * 64)
    monkeypatch.delenv("PAYMENTS_API_JWT_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="half-configured"):
        streamable_http.run()
