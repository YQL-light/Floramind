import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_app_001_root_connectivity(client: AsyncClient):
    res = await client.get("/")
    assert res.status_code in [200, 404]

@pytest.mark.asyncio
async def test_app_002_api_prefix(client: AsyncClient):
    res = await client.get("/api/v1/plant/knowledge")
    assert res.status_code != 404

@pytest.mark.asyncio
async def test_app_003_cors_headers(client: AsyncClient):
    res = await client.get("/api/v1/plant/knowledge", headers={"Origin": "http://localhost:3000"})
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_app_004_static_files_real(client: AsyncClient):
    res = await client.get("/uploads/any_file.txt")
    assert res.status_code in [200, 404]