# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict  # 1. 修改导入源


class Settings(BaseSettings):
    PROJECT_NAME: str = "植悟 ZhiWu"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # 数据库配置
    DATABASE_URL: str = "postgres://test:Bigdata@123@124.71.227.181:26000/zhiwu"

    # 2. Pydantic v2 的新配置写法 (用来替代 class Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 忽略环境变量中多余的字段，防止报错
    )


settings = Settings()