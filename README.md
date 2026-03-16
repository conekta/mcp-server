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
