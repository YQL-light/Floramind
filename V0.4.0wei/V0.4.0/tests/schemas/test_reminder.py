import pytest
from pydantic import ValidationError
from datetime import date
from app.schemas.reminder import PlantOut, PlantCreate, ReminderItem

def test_sch_r_001_plant_create_defaults():
    data = {
        "nickname": "测试多肉",
        "species": "景天科"
    }
    plant = PlantCreate(**data)
    assert plant.water_cycle == 7
    assert plant.nickname == "测试多肉"

def test_sch_r_002_plant_out_from_attributes():
    class MockPlant:
        id = 99
        nickname = "发财树"
        species = "木棉科"
        icon = "🌳"
        plantAvatar_url = "https://example.com/avatar.png"
        water_cycle = 10
        fertilize_cycle = 30
        last_watered = date(2025, 12, 1)
        last_fertilized = None

    plant_out = PlantOut.model_validate(MockPlant())
    assert plant_out.id == 99
    assert plant_out.plantAvatar_url == "https://example.com/avatar.png"
    assert isinstance(plant_out.last_watered, date)

def test_sch_r_003_reminder_item_validation():
    data = {
        "plant_id": 1,
        "plant_name": "薄荷",
        "type": "water",
        "message": "该浇水了",
        "ai_message": "主人，你的薄荷口渴了，快去喂它喝水吧！",
        "days_overdue": 3,
        "urgency": "high",
        "due_date": "2025-12-25",
        "icon": "💧"
    }
    reminder = ReminderItem(**data)
    assert reminder.urgency == "high"
    assert reminder.ai_message is not None
    assert "薄荷" in reminder.ai_message

def test_sch_r_004_missing_required_field():
    with pytest.raises(ValidationError) as excinfo:
        PlantCreate(nickname="只有名字的植物")
    assert "species" in str(excinfo.value)