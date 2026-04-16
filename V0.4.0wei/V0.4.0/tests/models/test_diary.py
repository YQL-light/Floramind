import pytest
from datetime import date
from app.models.user import User
from app.models.plant import Plant
from app.models.diary import Diary
from tortoise.exceptions import DoesNotExist

@pytest.fixture(scope="function")
async def diary_test_setup():
    await Diary.all().delete()
    await Plant.all().delete()
    await User.all().delete()
    
    user = await User.create(username="writer", email="w@test.com", password="p")
    plant = await Plant.create(user=user, nickname="小茉莉", species="茉莉")
    yield user, plant

@pytest.mark.asyncio
async def test_mod_d_001_multi_relation(diary_test_setup):
    user, plant = diary_test_setup
    diary = await Diary.create(
        user=user, 
        plant=plant, 
        content="今天长了一片新叶子", 
        diary_date=date.today()
    )
    assert diary.user.id == user.id
    assert diary.plant.id == plant.id

@pytest.mark.asyncio
async def test_mod_d_002_json_images(diary_test_setup):
    user, plant = diary_test_setup
    img_list = ["http://oss.com/1.jpg", "http://oss.com/2.jpg"]
    
    diary = await Diary.create(
        user=user, 
        plant=plant, 
        content="有图有真相", 
        diary_date=date.today(),
        images=img_list
    )
    
    db_diary = await Diary.get(id=diary.id)
    assert len(db_diary.images) == 2
    assert db_diary.images[0] == "http://oss.com/1.jpg"

@pytest.mark.asyncio
async def test_mod_d_003_default_weather(diary_test_setup):
    user, plant = diary_test_setup
    diary = await Diary.create(
        user=user, plant=plant, content="默认天气测试", diary_date=date.today()
    )
    assert diary.weather == "sunny"

@pytest.mark.asyncio
async def test_mod_d_004_cascade_delete_by_plant(diary_test_setup):
    user, plant = diary_test_setup
    diary = await Diary.create(
        user=user, plant=plant, content="随植物而去", diary_date=date.today()
    )
    
    await plant.delete()
    
    with pytest.raises(DoesNotExist):
        await Diary.get(id=diary.id)