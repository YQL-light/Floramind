import uvicorn
import os
import asyncpg.connection  # 华为云补丁依赖
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

# 确保导入了正确的 settings
from app.core.config import settings
from app.api.v1.api import api_router

# ==========================================================
# 【华为云 GaussDB/OpenGauss 兼容性补丁】保持不变
# ==========================================================
async def override_reset(self, timeout=None):
    pass
asyncpg.connection.Connection.reset = override_reset
# ==========================================================

# 确保 uploads 目录存在
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title=settings.PROJECT_NAME)

# 配置跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
# 注意：确保 settings.API_V1_STR 在 config.py 中已定义 (通常是 "/api/v1")
app.include_router(api_router, prefix=settings.API_V1_STR)

# 挂载静态目录
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ==========================================================
# 【重点修改这里】注册数据库 (Tortoise ORM)
# ==========================================================
register_tortoise(
    app,
    db_url=settings.DATABASE_URL,
    modules={
        # 这里必须包含所有存放 Model 的路径
        "models": ["app.models.user", "app.models.plant", "app.models.diary"]
    },
    generate_schemas=False, # 自动建表（生产环境建议改为False，使用aerich迁移工具）
    add_exception_handlers=True,
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)