import pytest

@pytest.mark.asyncio
async def test_api_a_001(authenticated_client):
    res = await authenticated_client.get("/api/v1/plant/knowledge")
    assert res.status_code == 200
    assert "knowledge" in res.json()

@pytest.mark.asyncio
async def test_api_a_002(authenticated_client):
    payload = {"question": "你好"}
    res = await authenticated_client.post("/api/v1/plant/chat", json=payload)
    assert res.status_code in [200, 400]
    if res.status_code == 200:
        assert "answer" in res.json() or "response" in res.json()

@pytest.mark.asyncio
async def test_api_a_003(authenticated_client):
    res = await authenticated_client.get("/api/v1/plant/conversations")
    assert res.status_code == 200
    assert "conversations" in res.json()