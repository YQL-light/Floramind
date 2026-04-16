import pytest
from app.models.user import User
from app.models.plant import Plant
from app.models.diary import Diary

@pytest.fixture(scope="function")
async def plant_test_setup():
    await Diary.all().delete()
    await Plant.all().delete()
    await User.all().delete()
    
    user = await User.create(username="botanist", email="b@test.com", password="p")
    yield user

@pytest.mark.asyncio
async def test_mod_p_001_create_plant(plant_test_setup):
    user = plant_test_setup
    plant = await Plant.create(
        user=user,
        nickname="小绿",
        species="绿萝"
    )
    assert plant.id is not None
    assert plant.user.id == user.id

@pytest.mark.asyncio
async def test_mod_p_002_default_values(plant_test_setup):
    user = plant_test_setup
    plant = await Plant.create(user=user, nickname="默认值测试", species="测试")
    if hasattr(plant, 'is_deleted'):
        assert plant.is_deleted is False

@pytest.mark.asyncio
async def test_mod_p_003_update_plant(plant_test_setup):
    user = plant_test_setup
    plant = await Plant.create(user=user, nickname="旧名字", species="旧种类")
    
    plant.nickname = "新名字"
    await plant.save()
    
    db_plant = await Plant.get(id=plant.id)
    assert db_plant.nickname == "新名字"

@pytest.mark.asyncio
async def test_mod_p_004_user_cascade_delete(plant_test_setup):
    from tortoise.exceptions import DoesNotExist
    user = plant_test_setup
    plant = await Plant.create(user=user, nickname="待消失", species="test")
    
    await user.delete()
    
    with pytest.raises(DoesNotExist):
        await Plant.get(id=plant.id)