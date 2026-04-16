import os
import asyncpg.connection  # 1. 导入 asyncpg

# ==========================================================
# 【重点】将补丁放到这里，确保 Aerich 运行时能加载到
# ==========================================================
async def override_reset(self, timeout=None):
    # 覆盖默认的 reset 方法，防止发送 OpenGauss 不支持的 UNLISTEN/DISCARD ALL 命令
    pass

asyncpg.connection.Connection.reset = override_reset
# ==========================================================

from app.core.config import settings

TORTOISE_ORM = {
    "connections": {
        "default": "postgres://test:Bigdata@123@124.71.227.181:26000/zhiwu",
    },
    "apps": {
        "models": {
            # 必须包含 aerich.models，以及你自己的模型路径
            "models": [
                "aerich.models",
                "app.models.user",
                "app.models.plant",
                "app.models.diary"
            ],
            "default_connection": "default",
        },
    },
}