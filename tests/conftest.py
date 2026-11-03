import pytest
import respx


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("CONEKTA_API_KEY", "test_key_abc123")  # gitleaks:allow


@pytest.fixture(autouse=True)
def reset_client():
    from conekta_mcp import auth, client, internal_auth

    auth.reset_api_key_provider()
    internal_auth.set_internal_config(None)
    client._client = None
    yield
    auth.reset_api_key_provider()
    internal_auth.set_internal_config(None)
    client._client = None


@pytest.fixture
def mock_api():
    with respx.mock(base_url="https://api.conekta.io") as respx_mock:
        yield respx_mock
