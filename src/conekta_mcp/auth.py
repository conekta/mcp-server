import os
from collections.abc import Callable

from mcp.server.lowlevel.server import request_ctx

from conekta_mcp.internal_auth import COMPANY_ID_HEADER, is_internal_token

ApiKeyProvider = Callable[[], str]
REQUEST_API_KEY_ERROR = (
    "Conekta API key is not set. Send it as Authorization: Bearer <key>."
)
INTERNAL_TOKEN_WITHOUT_COMPANY_ERROR = (
    f"The internal service credential requires the {COMPANY_ID_HEADER} header."
)


def get_env_api_key() -> str:
    key = os.environ.get("CONEKTA_API_KEY")
    if not key:
        raise RuntimeError(
            "CONEKTA_API_KEY environment variable is not set. "
            "Set it to your Conekta API key before running the server."
        )
    return key


def get_request_header_api_key() -> str:
    try:
        request_context = request_ctx.get()
    except LookupError as exc:
        raise RuntimeError(REQUEST_API_KEY_ERROR) from exc

    request = request_context.request
    if request is None:
        raise RuntimeError(REQUEST_API_KEY_ERROR)

    authorization = request.headers.get("authorization")
    if not authorization:
        raise RuntimeError(REQUEST_API_KEY_ERROR)

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise RuntimeError("Authorization header must use Bearer token format.")
    if is_internal_token(token):
        # Never forward the internal service credential to the public API.
        raise RuntimeError(INTERNAL_TOKEN_WITHOUT_COMPANY_ERROR)
    return token


_api_key_provider: ApiKeyProvider = get_env_api_key


def set_api_key_provider(provider: ApiKeyProvider) -> None:
    global _api_key_provider
    _api_key_provider = provider


def reset_api_key_provider() -> None:
    set_api_key_provider(get_env_api_key)


def get_api_key() -> str:
    return _api_key_provider()
