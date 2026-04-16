import pytest
from pydantic import ValidationError
from app.schemas.user import UserRegister, UserLogin, Token, BaseResponse, ResetPasswordRequest

def test_sch_u_001_user_register_valid():
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "security_answer": "我的母校"
    }
    user = UserRegister(**data)
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.security_answer == "我的母校"

def test_sch_u_002_user_register_invalid_email():
    data = {
        "username": "testuser",
        "email": "invalid-email", 
        "password": "password123",
        "security_answer": "answer"
    }
    with pytest.raises(ValidationError) as excinfo:
        UserRegister(**data)
    assert "value is not a valid email address" in str(excinfo.value)

def test_sch_u_003_base_response_flexibility():
    resp_dict = BaseResponse(code=200, msg="success", data={"id": 1})
    assert resp_dict.data["id"] == 1
    
    resp_list = BaseResponse(code=200, msg="success", data=[1, 2, 3])
    assert len(resp_list.data) == 3

def test_sch_u_004_reset_password_missing_field():
    data = {
        "account": "testuser",
        "new_password": "newpassword123"
    }
    with pytest.raises(ValidationError) as excinfo:
        ResetPasswordRequest(**data)
    assert "security_answer" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)

def test_sch_u_005_token_valid():
    data = {
        "access_token": "jwt_string",
        "token_type": "bearer",
        "user_id": 1,
        "username": "admin"
    }
    token = Token(**data)
    assert token.user_id == 1
    assert token.username == "admin"