import pytest
from pydantic import ValidationError
from app.schemas.diary import DiaryCreate, DiaryItem

def test_sch_d_001_diary_create_plant_id_string():
    data = {
        "plantId": "1001",
        "content": "今天绿萝长出了新芽，真开心！",
        "photos": ["https://example.com/p1.jpg"]
    }
    diary = DiaryCreate(**data)
    assert diary.plantId == "1001"
    assert "新芽" in diary.content

def test_sch_d_002_photo_list_validation():
    data = {
        "plantId": "1",
        "content": "多图上传测试",
        "photos": [
            "https://example.com/image1.png",
            "https://example.com/image2.png"
        ]
    }
    diary = DiaryCreate(**data)
    assert len(diary.photos) == 2
    assert diary.photos[0] == "https://example.com/image1.png"

def test_sch_d_003_diary_item_optional_fields():
    data = {
        "id": "50",
        "plantId": "1",
        "date": "2025-12-21",
        "content": "简单的日记内容",
        "photos": []
    }
    diary_item = DiaryItem(**data)
    
    assert diary_item.id == "50"
    if hasattr(diary_item, 'mood'):
        assert diary_item.mood is None