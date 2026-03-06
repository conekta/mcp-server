from conekta_mcp.server import mcp

import conekta_mcp.tools  # noqa: F401

if __name__ == "__main__":
    mcp.run(transport="stdio")
