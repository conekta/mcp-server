import json

import httpx
import pytest

from conekta_mcp.tools.subscriptions import (
    cancel_subscription,
    create_subscription,
    get_subscription,
    list_subscriptions,
    pause_subscription,
    resume_subscription,
    update_subscription,
)


@pytest.mark.asyncio
async def test_list_subscriptions(mock_api):
    mock_api.get("/customers/cus_1/subscriptions").mock(
        return_value=httpx.Response(
            200, json={"has_more": False, "data": [{"id": "sub_1"}]}
        )
    )
    result = await list_subscriptions("cus_1")
    data = json.loads(result)
    assert data["data"][0]["id"] == "sub_1"


@pytest.mark.asyncio
async def test_get_subscription(mock_api):
    mock_api.get("/customers/cus_1/subscriptions/sub_1").mock(
        return_value=httpx.Response(200, json={"id": "sub_1", "status": "active"})
    )
    result = await get_subscription("cus_1", "sub_1")
    data = json.loads(result)
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_subscription(mock_api):
    mock_api.post("/customers/cus_1/subscriptions").mock(
        return_value=httpx.Response(201, json={"id": "sub_new"})
    )
    result = await create_subscription("cus_1", plan_id="plan_1")
    data = json.loads(result)
    assert data["id"] == "sub_new"


@pytest.mark.asyncio
async def test_update_subscription(mock_api):
    mock_api.put("/customers/cus_1/subscriptions/sub_1").mock(
        return_value=httpx.Response(200, json={"id": "sub_1", "plan_id": "plan_2"})
    )
    result = await update_subscription("cus_1", "sub_1", plan_id="plan_2")
    data = json.loads(result)
    assert data["plan_id"] == "plan_2"


@pytest.mark.asyncio
async def test_update_subscription_no_fields():
    result = await update_subscription("cus_1", "sub_1")
    data = json.loads(result)
    assert data["error"] is True


@pytest.mark.asyncio
async def test_cancel_subscription(mock_api):
    mock_api.post("/customers/cus_1/subscriptions/sub_1/cancel").mock(
        return_value=httpx.Response(200, json={"id": "sub_1", "status": "cancelled"})
    )
    result = await cancel_subscription("cus_1", "sub_1")
    data = json.loads(result)
    assert data["status"] == "cancelled"


@pytest.mark.asyncio
async def test_pause_subscription(mock_api):
    mock_api.post("/customers/cus_1/subscriptions/sub_1/pause").mock(
        return_value=httpx.Response(200, json={"id": "sub_1", "status": "paused"})
    )
    result = await pause_subscription("cus_1", "sub_1")
    data = json.loads(result)
    assert data["status"] == "paused"


@pytest.mark.asyncio
async def test_resume_subscription(mock_api):
    mock_api.post("/customers/cus_1/subscriptions/sub_1/resume").mock(
        return_value=httpx.Response(200, json={"id": "sub_1", "status": "active"})
    )
    result = await resume_subscription("cus_1", "sub_1")
    data = json.loads(result)
    assert data["status"] == "active"
