import pytest
from tortoise.exceptions import IntegrityError
from app.models.user import User
from app.models.plant import Plant
from app.models.diary import Diary

@pytest.fixture(scope="function")
async def db_setup_direct():
    await Diary.all().delete()
    await Plant.all().delete()
    await User.all().delete()
    
    test_user = await User.create(
        username="testuser",
        email="test@example.com",
        password="hashedpassword"
    )
    yield test_user

@pytest.mark.asyncio
async def test_mod_u_001_create_user(db_setup_direct):
    user = db_setup_direct
    assert user is not None
    assert user.username == "testuser"

@pytest.mark.asyncio
async def test_mod_u_002_username_unique(db_setup_direct):
    with pytest.raises(IntegrityError):
        await User.create(username="testuser", email="other@e.com", password="p")

@pytest.mark.asyncio
async def test_mod_u_003_email_unique(db_setup_direct):
    with pytest.raises(IntegrityError):
        await User.create(username="other", email="test@example.com", password="p")

@pytest.mark.asyncio
async def test_mod_u_004_update_user(db_setup_direct):
    user = db_setup_direct
    user.location_city = "Beijing"
    await user.save()
    
    db_user = await User.get(id=user.id)
    assert db_user.location_city == "Beijing"

@pytest.mark.asyncio
async def test_mod_u_005_default_is_deleted(db_setup_direct):
    user = db_setup_direct
    assert user.is_deleted is False