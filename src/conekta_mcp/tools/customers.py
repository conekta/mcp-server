from conekta_mcp.client import build_params, conekta_get, conekta_request
from conekta_mcp.server import mcp


@mcp.tool()
async def create_customer(
    name: str,
    email: str,
    phone: str,
    custom_reference: str | None = None,
) -> str:
    """Create a new customer.

    Args:
        name: Customer full name
        email: Customer email address
        phone: Customer phone in E.164 format (e.g., +5215555555555)
        custom_reference: Optional custom reference for your system
    """
    body: dict = {"name": name, "email": email, "phone": phone}
    if custom_reference:
        body["custom_reference"] = custom_reference
    return await conekta_request("POST", "/customers", body=body)


@mcp.tool()
async def list_customers(
    limit: int = 20,
    search: str | None = None,
    next_page: str | None = None,
    previous_page: str | None = None,
) -> str:
    """List customers with optional search and pagination.

    Args:
        limit: Max number of customers to return (1-250, default 20)
        search: Search by name, email, phone, or custom reference
        next_page: Cursor for next page (from previous response)
        previous_page: Cursor for previous page (from previous response)
    """
    params = build_params(
        limit=limit, search=search, next=next_page, previous=previous_page
    )
    return await conekta_get("/customers", params=params)


@mcp.tool()
async def get_customer(customer_id: str) -> str:
    """Get a customer by ID.

    Args:
        customer_id: The Conekta customer ID (e.g., cus_2tXyF9BwPG14UMkAA)
    """
    return await conekta_get(f"/customers/{customer_id}")


@mcp.tool()
async def update_customer(
    customer_id: str,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    custom_reference: str | None = None,
) -> str:
    """Update an existing customer. Only provided fields are updated.

    Args:
        customer_id: The Conekta customer ID
        name: New customer name
        email: New customer email
        phone: New customer phone
        custom_reference: New custom reference
    """
    body = build_params(
        name=name, email=email, phone=phone, custom_reference=custom_reference
    )
    if not body:
        return '{"error": true, "message": "No fields provided to update"}'
    return await conekta_request("PUT", f"/customers/{customer_id}", body=body)
