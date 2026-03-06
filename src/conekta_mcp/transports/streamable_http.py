from conekta_mcp.auth import get_request_header_api_key, set_api_key_provider
from conekta_mcp.server import mcp

import conekta_mcp.tools  # noqa: F401


def run() -> None:
    set_api_key_provider(get_request_header_api_key)
    mcp.run(transport="streamable-http")
