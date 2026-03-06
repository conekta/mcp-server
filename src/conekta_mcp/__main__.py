from __future__ import annotations

import argparse
import os

from conekta_mcp.server import mcp

import conekta_mcp.tools  # noqa: F401


def _get_env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Conekta MCP server over stdio, SSE, or Streamable HTTP."
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default=_get_env("CONEKTA_MCP_TRANSPORT", "MCP_TRANSPORT", default="stdio"),
        help="Transport to expose. Defaults to stdio.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
