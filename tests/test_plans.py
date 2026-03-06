import json

import httpx
import pytest

from conekta_mcp.tools.plans import create_plan, get_plan, list_plans


@pytest.mark.asyncio
async def test_create_plan(mock_api):
    mock_api.post("/plans").mock(
        return_value=httpx.Response(
            201, json={"id": "plan_1", "name": "Monthly"}
        )
    )
    result = await create_plan(
        name="Monthly", amount=9900, currency="MXN", interval="month"
    )
    data = json.loads(result)
    assert data["id"] == "plan_1"


@pytest.mark.asyncio
async def test_list_plans(mock_api):
    mock_api.get("/plans").mock(
        return_value=httpx.Response(
            200, json={"has_more": False, "data": [{"id": "plan_1"}]}
        )
    )
    result = await list_plans()
    data = json.loads(result)
    assert len(data["data"]) == 1


@pytest.mark.asyncio
async def test_get_plan(mock_api):
    mock_api.get("/plans/plan_1").mock(
        return_value=httpx.Response(200, json={"id": "plan_1"})
    )
    result = await get_plan("plan_1")
    data = json.loads(result)
    assert data["id"] == "plan_1"
