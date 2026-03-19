import pytest
from app.core.config import settings
from pydantic_settings import SettingsConfigDict

def test_core_c_001_project_name():
    assert settings.PROJECT_NAME == "植悟 ZhiWu"

def test_core_c_002_api_v1_str():
    assert settings.API_V1_STR == "/api/v1"

def test_core_c_003_critical_configs():
    assert settings.SECRET_KEY == "123456789"
    assert settings.DATABASE_URL is not None
    assert settings.DATABASE_URL.startswith("postgres://")

def test_core_c_004_pydantic_v2_config():
    assert isinstance(settings.model_config, dict)
    assert settings.model_config.get("env_file") == ".env"
    assert settings.model_config.get("extra") == "ignore"