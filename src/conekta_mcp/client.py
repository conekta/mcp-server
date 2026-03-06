import json
import os

import httpx

BASE_URL = "https://api.conekta.io"
CONTENT_TYPE = "application/vnd.conekta-v2.2.0+json"

_client: httpx.AsyncClient | None = None


def _get_api_key() -> str:
    key = os.environ.get("CONEKTA_API_KEY")
    if not key:
        raise RuntimeError(
            "CONEKTA_API_KEY environment variable is not set. "
            "Set it to your Conekta API key before running the server."
        )
    return key


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {_get_api_key()}",
                "Content-Type": CONTENT_TYPE,
                "Accept": CONTENT_TYPE,
                "Accept-Language": "en",
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


async def conekta_get(path: str, params: dict | None = None) -> str:
    try:
        response = await get_client().get(path, params=params)
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
    try:
        response = await get_client().request(method, path, json=body, params=params)
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
