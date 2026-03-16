# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-03-16

### Changed

- `create_checkout` now only supports `PaymentLink` type; removed `type` parameter and hardcoded it internally.
- `create_order` checkout parameter changed from JSON string to typed object supporting `Integration` and `HostedPayment` types, with per-type field validation.
- `create_order` `line_items`, `charges`, `shipping_lines`, and `metadata` parameters changed from JSON strings to typed objects (`OrderLineItem`, `OrderCharge`, `OrderShippingLine`, `Metadata`).
- `update_order` `metadata` parameter changed from JSON string to typed `Metadata` object.

### Added

- Added `order_checkout.py` with `IntegrationCheckout` and `HostedPaymentCheckout` typed schemas and validation logic.
- Added typed structs in dedicated files: `order_line_item.py`, `order_charge.py`, `order_shipping_line.py`, `metadata.py`.

### Removed

- Removed `on_demand_enabled` field from checkout schema.

## [0.2.0] - 2026-03-06

### Existing

- Kept support for the original local MCP server flow over `stdio`.
- Preserved the existing Conekta tools and local development workflow based on `CONEKTA_API_KEY`.

### Added

- Added support for running the server over `Streamable HTTP`.
- Added hosted usage through `https://mcp.conekta.com/mcp`.
- Added support for per-request Conekta API keys via `Authorization: Bearer key_xxx`.
- Added HTTP healthcheck support at `/ping` for infrastructure deployments.
