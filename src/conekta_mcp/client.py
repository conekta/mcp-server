import json
import os
from importlib.metadata import PackageNotFoundError, version

import httpx

from conekta_mcp.auth import get_api_key
from conekta_mcp.internal_auth import (
    audit_logger,
    current_internal_identity,
    get_internal_config,
    internal_request_target,
)

BASE_URL = os.getenv("CONEKTA_API_BASE_URL", "https://api.conekta.io")
CONTENT_TYPE = "application/vnd.conekta-v2.2.0+json"


def _get_user_agent() -> str:
    try:
        package_version = version("conekta-mcp")
    except PackageNotFoundError:
        package_version = "unknown"
    return f"conekta-mcp/{package_version}"


USER_AGENT = _get_user_agent()

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Accept": CONTENT_TYPE,
                "Accept-Language": "en",
                "User-Agent": USER_AGENT,
            },
            timeout=30.0,
        )
    return _client


def _format(data: dict | list | str) -> str:
    if isinstance(data, str):
        return data
    return json.dumps(data, indent=2, ensure_ascii=False)


def _try_parse_json(text: str) -> dict | str:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def build_params(**kwargs) -> dict:
    return {k: v for k, v in kwargs.items() if v is not None}


def _request_target(path: str) -> tuple[str, dict[str, str]]:
    """URL and auth headers for ``path``: internal mode or the caller's API key."""
    identity = current_internal_identity()
    if identity is None:
        return path, {"Authorization": f"Bearer {get_api_key()}"}

    config = get_internal_config()
    if config is None:  # pragma: no cover - the middleware never sets an identity without it
        raise RuntimeError("Internal mode is not configured.")
    return internal_request_target(config, identity, path)


def _audit(method: str, path: str, status: int | str) -> None:
    identity = current_internal_identity()
    if identity is None:
        return
    audit_logger.info(
        "internal_mode api_call method=%s path=%s company_id=%s caller=%s status=%s",
        method,
        path,
        identity.company_id,
        identity.caller,
        status,
    )


async def conekta_get(path: str, params: dict | None = None) -> str:
    url, auth_headers = _request_target(path)
    try:
        response = await get_client().get(url, params=params, headers=auth_headers)
        _audit("GET", path, response.status_code)
        response.raise_for_status()
        return _format(response.json())
    except httpx.HTTPStatusError as e:
        return _format({
            "error": True,
            "status_code": e.response.status_code,
            "message": f"Conekta API error: {e.response.status_code}",
            "details": _try_parse_json(e.response.text),
        })
    except httpx.RequestError as e:
        return _format({"error": True, "message": f"Request failed: {e}"})


async def conekta_request(
    method: str,
    path: str,
    body: dict | None = None,
    params: dict | None = None,
) -> str:
    url, auth_headers = _request_target(path)
    try:
        response = await get_client().request(
            method,
            url,
            json=body,
            params=params,
            headers=auth_headers,
        )
        _audit(method, path, response.status_code)
        response.raise_for_status()
        if response.status_code == 204:
            return _format({"success": True})
        return _format(response.json())
    except httpx.HTTPStatusError as e:
        return _format({
            "error": True,
            "status_code": e.response.status_code,
            "message": f"Conekta API error: {e.response.status_code}",
            "details": _try_parse_json(e.response.text),
        })
    except httpx.RequestError as e:
        return _format({"error": True, "message": f"Request failed: {e}"})
