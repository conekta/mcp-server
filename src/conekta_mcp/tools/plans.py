from conekta_mcp.client import build_params, conekta_get, conekta_request
from conekta_mcp.server import mcp


@mcp.tool()
async def create_plan(
    name: str,
    amount: int,
    currency: str,
    interval: str,
    frequency: int = 1,
    trial_period_days: int | None = None,
    expiry_count: int | None = None,
) -> str:
    """Create a subscription plan.

    Args:
        name: Plan name
        amount: Plan price in cents
        currency: ISO currency code (e.g., MXN, USD)
        interval: Billing interval (day, week, half_month, month, year)
        frequency: How often the interval repeats (default 1)
        trial_period_days: Number of trial days before first charge
        expiry_count: Number of billing cycles before plan expires
    """
    body: dict = {
        "name": name,
        "amount": amount,
        "currency": currency,
        "interval": interval,
        "frequency": frequency,
    }
    if trial_period_days is not None:
        body["trial_period_days"] = trial_period_days
    if expiry_count is not None:
        body["expiry_count"] = expiry_count
    return await conekta_request("POST", "/plans", body=body)


@mcp.tool()
async def list_plans(
    limit: int = 20,
    search: str | None = None,
    next_page: str | None = None,
    previous_page: str | None = None,
) -> str:
    """List subscription plans with optional search and pagination.

    Args:
        limit: Max plans to return (1-250, default 20)
        search: Search by plan name
        next_page: Cursor for next page
        previous_page: Cursor for previous page
    """
    params = build_params(
        limit=limit, search=search, next=next_page, previous=previous_page
    )
    return await conekta_get("/plans", params=params)


@mcp.tool()
async def get_plan(plan_id: str) -> str:
    """Get a subscription plan by ID.

    Args:
        plan_id: The Conekta plan ID
    """
    return await conekta_get(f"/plans/{plan_id}")
