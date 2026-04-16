import pytest

@pytest.mark.asyncio
async def test_api_r_001(authenticated_client):
    payload = {
        "name": "绿萝", "nickname": "小绿", "species": "绿萝",
        "water_interval": 3, "image_url": "test.jpg", "last_watered": "2025-12-21"
    }
    res = await authenticated_client.post("/api/v1/plants", json=payload)
    assert res.status_code == 200
    assert "plant_id" in str(res.json())

@pytest.mark.asyncio
async def test_api_r_002(authenticated_client):
    res = await authenticated_client.get("/api/v1/reminders")
    assert res.status_code == 200
    assert "data" in res.json()

@pytest.mark.asyncio
async def test_api_r_003(authenticated_client):
    p = {"name": "A", "nickname": "B", "species": "C", "water_interval": 1}
    setup_res = await authenticated_client.post("/api/v1/plants", json=p)
    plant_id = setup_res.json()["data"]["plant_id"]
    
    res = await authenticated_client.post(f"/api/v1/plants/{plant_id}/water")
    assert res.status_code == 200
    assert "成功" in res.json().get("msg", "")

@pytest.mark.asyncio
async def test_api_r_004(authenticated_client):
    res = await authenticated_client.post("/api/v1/plants/99999/water")
    if res.status_code == 200:
        assert res.json().get("code") != 200
    else:
        assert res.status_code == 404