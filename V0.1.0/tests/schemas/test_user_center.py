import pytest
from pydantic import ValidationError
from app.schemas.user_center import UserStats, PasswordChange

def test_sch_c_001_user_stats_valid():
    data = {
        "plantCount": 5,
        "diaryCount": 12,
        "careDays": 30
    }
    stats = UserStats(**data)
    assert stats.plantCount == 5
    assert isinstance(stats.careDays, int)

    with pytest.raises(ValidationError):
        UserStats(plantCount="多肉", diaryCount=10, careDays=5)

def test_sch_c_002_password_change_missing_field():
    data = {
        "newPassword": "new_secure_password123"
    }
    with pytest.raises(ValidationError) as excinfo:
        PasswordChange(**data)
    
    assert "oldPassword" in str(excinfo.value)

def test_sch_c_002_password_change_success():
    data = {
        "oldPassword": "old_password_123",
        "newPassword": "new_password_456"
    }
    pw_change = PasswordChange(**data)
    assert pw_change.newPassword == "new_password_456"