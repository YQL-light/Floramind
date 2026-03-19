import pytest
from app.models.user import User
from app.core.security import get_password_hash

@pytest.mark.asyncio
async def test_api_u_001(client):
    payload = {"username": "new_user_888", "email": "888@test.com", "password": "123", "security_answer": "ans", "location_city": "BJ"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_api_u_002(client):
    await User.create(username="duplicate_user", email="dup@test.com", password=get_password_hash("123"), security_answer="ans", location_city="BJ")
    payload = {"username": "duplicate_user", "email": "other@test.com", "password": "123", "security_answer": "ans", "location_city": "BJ"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.json()["code"] == 400

@pytest.mark.asyncio
async def test_api_u_003(client):
    pwd = "test_password_123"
    await User.create(username="login_user", email="login@test.com", password=get_password_hash(pwd), security_answer="ans", location_city="BJ")
    payload = {"account": "login_user", "password": pwd}
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.json()["code"] == 200
    assert "access_token" in response.json()["data"]

@pytest.mark.asyncio
async def test_api_u_004(authenticated_client):
    path = "/api/v1/user_center/profile"
    response = await authenticated_client.get(path)
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["code"] == 200
    assert res_json["data"]["nickname"] == "tester"