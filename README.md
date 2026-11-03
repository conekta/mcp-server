# Conekta MCP Server

MCP server for the [Conekta](https://conekta.com) payment API. Exposes Conekta's core payment operations as tools for the [Model Context Protocol](https://modelcontextprotocol.io).

## Setup

```bash
# Install dependencies
uv sync

# Set your Conekta API key
export CONEKTA_API_KEY=key_your_api_key

# Run the server
uv run python -m conekta_mcp
```

By default the server uses the `stdio` transport for local MCP clients such as Claude Desktop.

## Hosted MCP

The server is available remotely over Streamable HTTP at:

```text
https://mcp.conekta.com/mcp
```

Use this endpoint if you want to connect to the hosted Conekta MCP server.
Send your Conekta API key in the request header:

```text
Authorization: Bearer key_xxx
```

### Configuration (Hosted / Streamable HTTP)

If your MCP client supports remote servers over HTTP, the JSON config should include the hosted URL and the `Authorization` header.

Example:

```json
{
  "mcpServers": {
    "conekta": {
      "url": "https://mcp.conekta.com/mcp",
      "headers": {
        "Authorization": "Bearer key_xxx"
      }
    }
  }
}
```

Notes:

- Replace `key_xxx` with your real Conekta private API key.
- The header must be exactly `Authorization`.
- The value must include the `Bearer ` prefix.

### Claude Code (CLI)

```bash
claude mcp add --transport http conekta https://mcp.conekta.com/mcp \
  --header "Authorization: Bearer key_xxx"
```

Replace `key_xxx` with your real Conekta private API key.

## Internal mode (Conekta services only)

Trusted Conekta services (today, the payment agent bot) can operate as a company without its private API key. This is not available to merchants.

The caller sends:

```text
Authorization: Bearer <CONEKTA_MCP_INTERNAL_TOKEN>
X-Company-Id: <company_id>
```

The server then calls payments-api at `PAYMENTS_API_INTERNAL_URL` + `/internal/api/<public path>` with a 60-second HS256 JWT signed with payments-api's `JWT_SECRET` and a fresh `X-Company-Context` (AES-256-GCM, see payments-api `lib/auth/internal_company_context.rb`). Checkouts are created with `livemode: true`.

| Variable | Description |
|---|---|
| `CONEKTA_MCP_INTERNAL_TOKEN` | Service credential shared with the caller (at least 32 characters; `openssl rand -hex 32`, different per environment). |
| `PAYMENTS_API_JWT_SECRET` | payments-api `JWT_SECRET` of the same environment. |
| `PAYMENTS_API_INTERNAL_URL` | payments-api base URL reachable for `/internal/api` (no trailing `/internal/api`). |
| `CONEKTA_MCP_INTERNAL_CALLER` | Optional caller name for audit logs and the JWT `sub`. Defaults to `conekta-payment-agent`. |

Behavior:

- No feature flag. With neither secret set, every request with `X-Company-Id` gets `401` and public mode works as before. With only one of `CONEKTA_MCP_INTERNAL_TOKEN` / `PAYMENTS_API_JWT_SECRET`, or without `PAYMENTS_API_INTERNAL_URL`, the server refuses to start.
- A request with `X-Company-Id` and an invalid credential gets `401` at the HTTP layer, before any MCP session; it never falls back to public mode.
- The internal credential without `X-Company-Id` can list tools, but any tool call fails without reaching the API.
- Only `create_checkout` is listed and callable in internal mode.
- Every internal tool call and API call is logged by the `conekta_mcp.audit` logger with `company_id` and caller.
- Load these secrets only on an instance or route reachable from the internal network: `PAYMENTS_API_JWT_SECRET` lets the holder act as any company in payments-api's internal API.

## Configuration (Claude Desktop / stdio)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "conekta": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/mcp", "run", "python", "-m", "conekta_mcp"],
      "env": {
        "CONEKTA_API_KEY": "key_your_api_key"
      }
    }
  }
}
```

## Available Tools

| Resource | Tools |
|----------|-------|
| Balance | `get_balance` |
| Customers | `create_customer`, `list_customers`, `get_customer`, `update_customer` |
| Orders | `create_order`, `list_orders`, `get_order`, `update_order`, `cancel_order`, `capture_order` |
| Charges | `list_charges` |
| Refunds | `create_refund` |
| Plans | `create_plan`, `list_plans`, `get_plan` |
| Subscriptions | `list_subscriptions`, `get_subscription`, `create_subscription`, `update_subscription`, `cancel_subscription`, `pause_subscription`, `resume_subscription` |
| Checkouts | `create_checkout`, `list_checkouts`, `get_checkout`, `cancel_checkout`, `send_checkout_email`, `send_checkout_sms` |
| Events | `list_events`, `get_event` |
| Companies | `get_current_company` |

## Docker

```bash
docker run --pull=always -i --rm \
  -e CONEKTA_API_KEY=key_your_api_key \
  ghcr.io/conekta/mcp-server:latest
```

### Configuration (Claude Desktop with Docker / stdio)

```json
{
  "mcpServers": {
    "conekta": {
      "command": "docker",
      "args": ["run", "--pull=always", "-i", "--rm", "-e", "CONEKTA_API_KEY", "ghcr.io/conekta/mcp-server:latest"],
      "env": {
        "CONEKTA_API_KEY": "key_your_api_key"
      }
    }
  }
}
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v
```
