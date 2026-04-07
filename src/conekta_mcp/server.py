import logging
import os

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class _HealthCheckFilter(logging.Filter):
    """Filter out /ping access logs to reduce noise from K8s health checks."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "/ping" not in record.getMessage()


logging.getLogger("uvicorn.access").addFilter(_HealthCheckFilter())


def _get_env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"

mcp = FastMCP(
    "conekta",
    instructions=(
        "Conekta Payment API server. Provides tools to manage customers, "
        "orders, charges, subscriptions, plans, checkouts, and other "
        "Conekta payment resources. Requires a Conekta API key either via "
        "Authorization Bearer header or CONEKTA_API_KEY environment variable."
    ),
    host=_get_env("CONEKTA_MCP_HOST", "127.0.0.1"),
    port=_get_int_env("CONEKTA_MCP_PORT", 8000),
    streamable_http_path=_normalize_path(
        _get_env("CONEKTA_MCP_STREAMABLE_HTTP_PATH", "/mcp")
    ),
)


@mcp.custom_route("/ping", methods=["GET"], include_in_schema=False)
async def ping(_: Request) -> Response:
    return JSONResponse({"status": "ok"})
