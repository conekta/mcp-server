from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "conekta",
    instructions=(
        "Conekta Payment API server. Provides tools to manage customers, "
        "orders, charges, subscriptions, plans, checkouts, and other "
        "Conekta payment resources. Requires CONEKTA_API_KEY environment variable."
    ),
)
