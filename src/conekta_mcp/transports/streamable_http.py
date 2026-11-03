import uvicorn
from starlette.applications import Starlette

from conekta_mcp.auth import get_request_header_api_key, set_api_key_provider
from conekta_mcp.internal_auth import (
    InternalAuthMiddleware,
    configure_audit_logging,
    load_internal_config,
    set_internal_config,
)
from conekta_mcp.server import mcp
from conekta_mcp.tools import initialize


def build_app() -> Starlette:
    """Streamable HTTP app with internal mode authenticated before any MCP session."""
    app = mcp.streamable_http_app()
    app.add_middleware(InternalAuthMiddleware)
    return app


def run() -> None:
    initialize()
    set_api_key_provider(get_request_header_api_key)
    # Fails fast when internal mode is half-configured.
    set_internal_config(load_internal_config())
    configure_audit_logging()

    config = uvicorn.Config(
        build_app(),
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
    uvicorn.Server(config).run()
