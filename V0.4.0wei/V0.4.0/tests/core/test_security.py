import pytest
from jose import jwt
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

def test_core_s_001_password_hash_consistency():
    pwd = "testpassword"
    h1 = get_password_hash(pwd)
    h2 = get_password_hash(pwd)
    assert h1 != h2

def test_core_s_002_password_verify_success():
    pwd = "correctpassword"
    h = get_password_hash(pwd)
    assert verify_password(pwd, h) is True

def test_core_s_003_password_verify_fail():
    pwd = "correctpassword"
    h = get_password_hash(pwd)
    assert verify_password("wrongpassword", h) is False

def test_core_s_004_password_hash_type():
    h = get_password_hash("test")
    assert isinstance(h, str)

def test_core_s_005_jwt_token_format():
    token = create_access_token(subject="user_123")
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

def test_core_s_006_jwt_decode_subject():
    subject = "test_user_id"
    token = create_access_token(subject)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload.get("sub") == subject

def test_core_s_007_jwt_algorithm_check():
    token = create_access_token(subject="test")
    header = jwt.get_unverified_header(token)
    assert header["alg"] == settings.ALGORITHM