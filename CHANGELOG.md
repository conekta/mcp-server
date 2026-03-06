# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-03-06

### Existing

- Kept support for the original local MCP server flow over `stdio`.
- Preserved the existing Conekta tools and local development workflow based on `CONEKTA_API_KEY`.

### Added

- Added support for running the server over `Streamable HTTP`.
- Added hosted usage through `https://mcp.conekta.com/mcp`.
- Added support for per-request Conekta API keys via `Authorization: Bearer key_xxx`.
- Added HTTP healthcheck support at `/ping` for infrastructure deployments.
