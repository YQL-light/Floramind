# app/api/v1/endpoints/reminder.py
import json
import re
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from datetime import date, timedelta, datetime
from pydantic import BaseModel
from typing import List, Optional, Dict
from app.models.diary import Diary
import aiohttp
import os
import uuid
import shutil
import httpx

# 导入依赖
from app.api.deps import get_current_user
from app.core.config import settings

# 导入模型和Schema
from app.models.plant import Plant
from app.models.user import User
from app.schemas.user import BaseResponse
from app.schemas.reminder import (
    ReminderItem,
    ReminderListResponse,
    PlantOperationResponse,
    PlantCreate,
    PlantOut
)


class PlantRecommendationReq(BaseModel):
    species: str


router = APIRouter()

# --- 配置 ---
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = "sk-17a01a6a51624698ba06dfdec42bec78"

# OpenWeatherMap 配置
WEATHER_API_KEY = "d7aadb72af4007994d98593361db009b"
WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# 配置上传目录
UPLOAD_DIR = "uploads"
PLANT_AVATAR_DIR_NAME = "plantAvatars"
PLANT_AVATAR_FULL_DIR = os.path.join(UPLOAD_DIR, PLANT_AVATAR_DIR_NAME)
DEFAULT_PLANT_AVATAR = f"{PLANT_AVATAR_DIR_NAME}/default_avatar.png"

# 确保目录存在
os.makedirs(PLANT_AVATAR_FULL_DIR, exist_ok=True)

# ========== 缓存 ==========
from functools import wraps

# 城市翻译缓存
city_translation_cache = {}

# 天气缓存
weather_cache = {}
WEATHER_CACHE_TTL = 3600  # 1小时

# AI 提醒文案缓存
ai_reminder_cache = {}
AI_REMINDER_CACHE_TTL = 1800  # 30分钟


def get_weather_cache_key(city: str) -> str:
    """生成天气缓存键"""
    return city.strip().lower()


def get_ai_reminder_cache_key(plant_name: str, action: str, overdue: int, humidity: int) -> str:
    """生成AI提醒缓存键"""
    return f"{plant_name}_{action}_{overdue}_{humidity}".lower()


# ========== 性能计时装饰器（修改后） ==========
import time


def log_performance(func_name: str = None):
    """性能日志装饰器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            name = func_name or func.__name__
            if elapsed > 500:
                print(f"⚠️ 慢操作: {name} - {elapsed:.2f}ms")
            else:
                print(f"✅ 正常: {name} - {elapsed:.2f}ms")
            return result

        return wrapper

    return decorator


# ========== 基于空气湿度的浇水周期计算器 ==========
from enum import Enum


class HumidityLevel(Enum):
    """湿度级别"""
    VERY_DRY = "非常干燥"  # < 30%
    DRY = "干燥"  # 30-40%
    COMFORTABLE = "舒适"  # 40-60%
    HUMID = "潮湿"  # 60-80%
    VERY_HUMID = "非常潮湿"  # > 80%


class PlantWaterNeed(Enum):
    """植物需水量"""
    LOW = "低"  # 多肉、仙人掌等
    MEDIUM = "中"  # 绿萝、吊兰等
    HIGH = "高"  # 蕨类、竹芋等


class HumidityAdaptiveCalculator:
    """基于空气湿度的浇水周期计算器"""

    def __init__(self):
        # 湿度系数（湿度越高，系数越大，周期越长）
        self.humidity_coefficient = {
            "very_dry": 0.6,  # < 30% → 周期缩短40%
            "dry": 0.75,  # 30-40% → 周期缩短25%
            "comfortable": 1.0,  # 40-60% → 正常周期
            "humid": 1.2,  # 60-80% → 周期延长20%
            "very_humid": 1.4  # > 80% → 周期延长40%
        }

        # 植物需水量修正系数
        self.plant_need_coefficient = {
            PlantWaterNeed.LOW: 1.3,  # 需水少 → 周期延长30%
            PlantWaterNeed.MEDIUM: 1.0,  # 需水适中 → 正常
            PlantWaterNeed.HIGH: 0.7  # 需水多 → 周期缩短30%
        }

        # 季节修正系数
        self.season_coefficient = {
            "spring": 1.0,  # 春季生长旺盛
            "summer": 0.85,  # 夏季蒸发快
            "autumn": 1.0,  # 秋季
            "winter": 1.2  # 冬季休眠期
        }

    def get_humidity_level(self, humidity: int) -> str:
        """根据湿度百分比返回级别"""
        if humidity < 30:
            return "very_dry"
        elif humidity < 40:
            return "dry"
        elif humidity < 60:
            return "comfortable"
        elif humidity < 80:
            return "humid"
        else:
            return "very_humid"

    def get_plant_water_need(self, species: str) -> PlantWaterNeed:
        """根据植物品种判断需水量"""
        species_lower = species.lower()

        # 低需水植物（多肉、沙漠植物）
        low_need = [
            "多肉", "仙人掌", "芦荟", "玉露", "生石花", "景天",
            "沙漠玫瑰", "龙舌兰", "金琥", "虎尾兰", "长寿花"
        ]
        if any(s in species_lower for s in low_need):
            return PlantWaterNeed.LOW

        # 高需水植物（蕨类、喜湿植物）
        high_need = [
            "蕨类", "铁线蕨", "波士顿蕨", "彩叶芋", "竹芋",
            "龟背竹", "春羽", "蔓绿绒", "海芋", "白掌", "一帆风顺"
        ]
        if any(s in species_lower for s in high_need):
            return PlantWaterNeed.HIGH

        # 中等需水（默认）
        return PlantWaterNeed.MEDIUM

    def get_season(self) -> str:
        """获取当前季节"""
        month = datetime.now().month
        if 3 <= month <= 5:
            return "spring"
        elif 6 <= month <= 8:
            return "summer"
        elif 9 <= month <= 11:
            return "autumn"
        else:
            return "winter"

    def calculate_watering_cycle(
            self,
            base_cycle: int,
            humidity: int,
            species: str,
            consider_season: bool = True
    ) -> Dict:
        """
        基于空气湿度计算动态浇水周期

        Returns:
            {
                "dynamic_cycle": 8.4,
                "base_cycle": 7,
                "adjustment_percent": 20,
                "humidity": {"value": 45, "level": "舒适", "coefficient": 1.0},
                "plant_need": {"type": "中", "coefficient": 1.0},
                "season": "spring",
                "combined_coefficient": 1.0,
                "adjustment_reason": "空气湿度舒适，可按正常周期养护",
                "recommendation": "按正常周期养护即可"
            }
        """
        # 1. 获取湿度级别和系数
        humidity_level = self.get_humidity_level(humidity)
        humidity_coef = self.humidity_coefficient[humidity_level]

        # 2. 获取植物需水量系数
        water_need = self.get_plant_water_need(species)
        plant_coef = self.plant_need_coefficient[water_need]

        # 3. 获取季节系数
        season_coef = 1.0
        season = None
        if consider_season:
            season = self.get_season()
            season_coef = self.season_coefficient[season]

        # 4. 计算综合系数
        combined_coef = humidity_coef * plant_coef * season_coef
        combined_coef = max(0.4, min(1.8, combined_coef))

        # 5. 计算动态周期
        dynamic_cycle = round(base_cycle * combined_coef, 1)

        # 6. 生成调整建议
        adjustment_reason, recommendation = self._generate_advice(
            humidity_level, water_need, combined_coef
        )

        return {
            "dynamic_cycle": dynamic_cycle,
            "base_cycle": base_cycle,
            "adjustment_percent": round((combined_coef - 1) * 100, 1),
            "humidity": {
                "value": humidity,
                "level": self._get_humidity_level_cn(humidity_level),
                "coefficient": humidity_coef
            },
            "plant_need": {
                "type": water_need.value,
                "coefficient": plant_coef
            },
            "season": season,
            "combined_coefficient": combined_coef,
            "adjustment_reason": adjustment_reason,
            "recommendation": recommendation
        }

    def _get_humidity_level_cn(self, level: str) -> str:
        """获取湿度级别中文名"""
        mapping = {
            "very_dry": "非常干燥",
            "dry": "干燥",
            "comfortable": "舒适",
            "humid": "潮湿",
            "very_humid": "非常潮湿"
        }
        return mapping.get(level, "舒适")

    def _generate_advice(
            self,
            humidity_level: str,
            water_need: PlantWaterNeed,
            combined_coef: float
    ) -> tuple:
        """生成建议文案"""
        # 根据湿度级别生成建议
        humidity_advice = {
            "very_dry": "空气非常干燥，水分蒸发快，需增加浇水频率",
            "dry": "空气较干燥，建议适当提前浇水",
            "comfortable": "空气湿度舒适，可按正常周期养护",
            "humid": "空气较潮湿，土壤干得慢，可适当延长浇水间隔",
            "very_humid": "空气非常潮湿，注意控制浇水，避免烂根"
        }

        # 根据需水量生成建议
        plant_advice = {
            PlantWaterNeed.LOW: "植物本身需水少，注意控水",
            PlantWaterNeed.MEDIUM: "植物需水量适中",
            PlantWaterNeed.HIGH: "植物喜湿，需保持土壤微润"
        }

        adjustment_reason = humidity_advice.get(humidity_level, "")

        # 生成具体操作建议
        if combined_coef < 0.7:
            recommendation = "建议提前2-3天浇水"
        elif combined_coef < 0.9:
            recommendation = "建议提前1-2天浇水"
        elif combined_coef > 1.3:
            recommendation = "建议延后2-3天浇水"
        elif combined_coef > 1.1:
            recommendation = "建议延后1-2天浇水"
        else:
            recommendation = "按正常周期养护即可"

        recommendation = f"{plant_advice[water_need]}，{recommendation}"

        return adjustment_reason, recommendation

    def get_watering_quality_advice(
            self,
            humidity: int,
            days_since_last_water: int,
            dynamic_cycle: float
    ) -> str:
        """
        获取浇水质量建议（判断是否浇水过早/过晚）
        """
        if dynamic_cycle <= 0:
            return "请先设置浇水周期"

        ratio = days_since_last_water / dynamic_cycle

        if ratio < 0.5:
            return "⚠️ 浇水频率过高，土壤可能长期过湿，容易导致烂根"
        elif ratio < 0.8:
            return "💧 土壤可能还湿润，建议再等1-2天再浇水"
        elif ratio < 1.0:
            return "🌱 接近最佳浇水时机，可以再等1天"
        elif ratio < 1.2:
            return "💚 最佳浇水时机！土壤干湿适宜"
        elif ratio < 1.5:
            return "🌿 轻微缺水，可以浇水了"
        else:
            return "🥀 严重缺水，请立即浇水！"


# --- 辅助函数 ---

def calculate_days_since(last_date: Optional[object]) -> int:
    """计算距离上次养护的天数"""
    if not last_date:
        return 999
    if isinstance(last_date, datetime):
        last_date = last_date.date()
    elif isinstance(last_date, date):
        pass
    else:
        return 999
    return (date.today() - last_date).days


def get_urgency_level(days_overdue: int, cycle: int) -> str:
    """计算紧急程度"""
    if days_overdue < 0:
        return "low"
    safe_cycle = cycle if cycle > 0 else 1
    ratio = days_overdue / safe_cycle
    if ratio > 0.5:
        return "high"
    if ratio > 0.2:
        return "medium"
    return "low"


def get_icon(operation_type: str, urgency: str) -> str:
    """获取图标"""
    base_icons = {"water": "💧", "fertilize": "🌱"}
    base = base_icons.get(operation_type, "🍃")
    if urgency == "high":
        return f"{base}🔥"
    if urgency == "medium":
        return f"{base}⏰"
    return base


def get_watering_icon(urgency: str, humidity: int) -> str:
    """根据紧急程度和湿度返回浇水图标"""
    if urgency == "high":
        return "💧🔥"
    elif urgency == "medium":
        if humidity < 40:
            return "💧🌵"
        return "💧⏰"
    elif urgency == "low":
        return "💧"
    else:
        if humidity > 70:
            return "💧⚠️"
        return "💧🌱"


async def translate_city_llm(city_name: str) -> str:
    """使用 LLM 将中文城市名转换为英文/拼音"""
    if city_name in city_translation_cache:
        return city_translation_cache[city_name]

    print(f"正在调用 LLM 翻译城市名: {city_name} ...")

    system_prompt = (
        "你是一个专业的地理翻译助手。请将用户输入的中文城市名称转换为用于 "
        "OpenWeatherMap API 的标准英文名称（通常是拼音）。"
        "要求：只返回英文名称，不要包含任何标点符号、解释或额外文本。"
        "例如：输入'北京'，返回'Beijing'；输入'西安'，返回'Xian'。"
    )

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": city_name}
                ],
                "temperature": 0.1,
                "max_tokens": 20
            }
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }

            response = await client.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=10.0)

            if response.status_code == 200:
                result = response.json()
                english_name = result["choices"][0]["message"]["content"].strip()
                english_name = re.sub(r'[^\w\s]', '', english_name)
                city_translation_cache[city_name] = english_name
                print(f"LLM翻译城市名为：{english_name}")
                return english_name
            else:
                print(f"LLM 翻译失败: {response.status_code}")
                return city_name
    except Exception as e:
        print(f"LLM 调用异常: {e}")
        return city_name


async def get_current_weather_detailed(city: str) -> Dict:
    """获取详细天气数据（包含湿度）"""
    if not city or city.strip() == "":
        city = "北京"

    cache_key = get_weather_cache_key(city)
    if cache_key in weather_cache:
        cached_time, cached_data = weather_cache[cache_key]
        if datetime.now() - cached_time < timedelta(seconds=WEATHER_CACHE_TTL):
            print(f"✅ 使用天气缓存: {city}")
            return cached_data

    api_city = await translate_city_llm(city)

    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "q": api_city,
                "appid": WEATHER_API_KEY,
                "units": "metric",
                "lang": "zh_cn"
            }
            async with session.get(WEATHER_BASE_URL, params=params, timeout=8) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    weather_detail = {
                        "city": city,
                        "weather_text": data["weather"][0]["description"],
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "wind_speed": data["wind"]["speed"],
                        "icon": data["weather"][0]["icon"]
                    }
                    weather_cache[cache_key] = (datetime.now(), weather_detail)
                    return weather_detail
                else:
                    print(f"天气API错误: {resp.status}")
    except asyncio.TimeoutError:
        print("天气API超时")
    except Exception as e:
        print(f"天气获取失败: {e}")

    # 返回默认数据
    return {
        "city": city,
        "weather_text": "晴",
        "temperature": 20,
        "feels_like": 20,
        "humidity": 50,
        "pressure": 1013,
        "wind_speed": 2.5,
        "icon": "01d"
    }


async def generate_watering_message(
        plant_name: str,
        days_overdue: int,
        humidity: int,
        humidity_level: str,
        recommendation: str,
        quality_advice: str
) -> str:
    """生成基于湿度的浇水提醒文案（带缓存）"""
    cache_key = get_ai_reminder_cache_key(plant_name, "water", days_overdue, humidity)
    if cache_key in ai_reminder_cache:
        cached_time, cached_msg = ai_reminder_cache[cache_key]
        if datetime.now() - cached_time < timedelta(seconds=AI_REMINDER_CACHE_TTL):
            return cached_msg

    # 根据湿度和逾期天数选择模板
    if days_overdue <= 0:
        if humidity > 70:
            msg = f"🌧️ 主人，今天空气湿度{humidity}%很潮湿，{recommendation}，记得检查土壤干湿情况再决定是否浇水哦~"
        elif humidity < 40:
            msg = f"🌵 主人，空气好干燥（{humidity}%），{recommendation}，我已经有点渴了！"
        else:
            msg = f"💚 主人，今天空气湿度{humidity}%，{recommendation}，记得来看看我哦~"
    elif days_overdue < 3:
        if humidity > 70:
            msg = f"🌿 主人，我还没浇水，但最近湿度高（{humidity}%），{recommendation}，不用着急~"
        elif humidity < 40:
            msg = f"🥺 主人，空气很干燥（{humidity}%），{recommendation}，我快渴了！"
        else:
            msg = f"💧 主人，{recommendation}，记得来看我呀~"
    else:
        if humidity > 70:
            msg = f"😥 主人，我都{days_overdue}天没浇水了，虽然湿度高（{humidity}%），但{quality_advice}"
        else:
            msg = f"🥀 主人救命！我都{days_overdue}天没浇水了，空气湿度{humidity}%，{quality_advice}"

    # 保存缓存
    ai_reminder_cache[cache_key] = (datetime.now(), msg)
    return msg


async def generate_smart_message(
        plant_name: str,
        action: str,
        days_overdue: int,
        weather: str
) -> str:
    """生成施肥提醒文案"""
    cache_key = get_ai_reminder_cache_key(plant_name, action, days_overdue, 0)
    if cache_key in ai_reminder_cache:
        cached_time, cached_msg = ai_reminder_cache[cache_key]
        if datetime.now() - cached_time < timedelta(seconds=AI_REMINDER_CACHE_TTL):
            return cached_msg

    if days_overdue > 7:
        msg = f"主人，我都{days_overdue}天没{action}了，快来看看我吧！🥺"
    elif days_overdue > 3:
        msg = f"主人，我已经{days_overdue}天没{action}了，有点不舒服呢...记得{action}哦~"
    else:
        msg = f"主人，今天天气{weather}，什么时候给我{action}呀？🌱"

    ai_reminder_cache[cache_key] = (datetime.now(), msg)
    return msg


async def get_plant_recommendation_from_ai(species: str) -> dict:
    """询问 AI 该植物的浇水和施肥周期"""
    system_prompt = """
    你是一个专业的植物养护专家。
    请根据用户提供的植物品种，推荐合理的"浇水周期（天）"和"施肥周期（天）"。

    要求：
    1. 必须返回纯 JSON 格式。
    2. JSON 格式必须包含两个字段：`water_cycle` (整数) 和 `fertilize_cycle` (整数)。
    3. 不要包含任何 markdown 格式，只返回 JSON 字符串。
    4. 如果植物品种不明确，给出保守的默认值（浇水7天，施肥30天）。
    """

    user_prompt = f"植物种类：{species}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 50
            }
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            async with session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=8) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    content = result["choices"][0]["message"]["content"].strip()
                    content = content.replace("```json", "").replace("```", "").strip()
                    return json.loads(content)
    except Exception as e:
        print(f"AI 推荐失败: {e}")

    return {"water_cycle": 7, "fertilize_cycle": 30}


def build_avatar_url(avatar_path: Optional[str]) -> str:
    """返回可访问的植物头像 URL"""
    path = avatar_path or DEFAULT_PLANT_AVATAR
    if path.startswith("http"):
        return path
    return f"/uploads/{path}"


async def process_with_limit(tasks, process_func, limit=3):
    """限制并发数量的包装器"""
    semaphore = asyncio.Semaphore(limit)

    async def bounded_task(task):
        async with semaphore:
            return await process_func(task)

    return await asyncio.gather(*[bounded_task(t) for t in tasks])


# ========== 路由定义 ==========

@router.get("/get_plants", response_model=BaseResponse)
async def get_user_plants(current_user: User = Depends(get_current_user)):
    """获取用户所有植物"""
    plants = await Plant.filter(user=current_user, is_deleted=False).order_by("-created_at").all()
    plant_data = [PlantOut.model_validate(p) for p in plants]
    return BaseResponse(code=200, msg="获取成功", data=plant_data)


@router.post("/upload_avatar", response_model=BaseResponse)
async def upload_plant_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    """上传植物头像"""
    if not file.content_type.startswith('image/'):
        return BaseResponse(code=400, msg="请上传图片文件")

    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_name = f"plant_{uuid.uuid4().hex}{file_ext}"
    file_save_path = os.path.join(PLANT_AVATAR_FULL_DIR, unique_name)
    db_path = f"{PLANT_AVATAR_DIR_NAME}/{unique_name}"

    try:
        with open(file_save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return BaseResponse(
            code=200,
            msg="图片上传成功",
            data={"url": db_path}
        )
    except Exception as e:
        return BaseResponse(code=500, msg=f"上传失败: {str(e)}")


@router.post("/plants", response_model=BaseResponse)
async def create_plant(
        plant_in: PlantCreate,
        current_user: User = Depends(get_current_user)
):
    """创建植物"""
    w_date = None
    if plant_in.last_watered:
        try:
            w_date = datetime.strptime(plant_in.last_watered, "%Y-%m-%d").date()
        except ValueError:
            pass

    f_date = None
    if plant_in.last_fertilized:
        try:
            f_date = datetime.strptime(plant_in.last_fertilized, "%Y-%m-%d").date()
        except ValueError:
            pass

    avatar_path = plant_in.plantAvatar_url or DEFAULT_PLANT_AVATAR

    try:
        plant = await Plant.create(
            user=current_user,
            nickname=plant_in.nickname,
            species=plant_in.species,
            water_cycle=plant_in.water_cycle,
            fertilize_cycle=plant_in.fertilize_cycle,
            last_watered=w_date,
            last_fertilized=f_date,
            plantAvatar_url=avatar_path
        )
    except Exception as e:
        return BaseResponse(code=500, msg=f"创建植物失败: {str(e)}")

    return BaseResponse(
        code=200,
        msg="植物添加成功",
        data={
            "plant_id": plant.id,
            "nickname": plant.nickname,
            "plantAvatar_url": build_avatar_url(plant.plantAvatar_url)
        }
    )


# ========== 核心提醒接口 - 移除装饰器避免问题 ==========
@router.get("/reminders", response_model=BaseResponse)
async def get_reminders(current_user: User = Depends(get_current_user)):
    """获取智能提醒列表（基于空气湿度的动态浇水周期）"""
    import time
    start_time = time.time()

    try:
        plants = await Plant.filter(user=current_user, is_deleted=False).all()

        if not plants:
            return BaseResponse(
                code=200,
                msg="获取成功",
                data={"reminders": [], "total": 0, "current_humidity": None, "humidity_level": None}
            )

        # 获取当前空气湿度
        user_city = current_user.location_city or "北京"
        weather_data = await get_current_weather_detailed(user_city)
        current_humidity = weather_data.get("humidity", 50)

        # 初始化湿度自适应计算器
        humidity_calc = HumidityAdaptiveCalculator()

        reminders = []

        for plant in plants:
            # ========== 浇水提醒（基于空气湿度） ==========
            if plant.water_cycle and plant.water_cycle > 0:
                # 1. 计算动态浇水周期
                dynamic = humidity_calc.calculate_watering_cycle(
                    base_cycle=plant.water_cycle,
                    humidity=current_humidity,
                    species=plant.species,
                    consider_season=True
                )

                # 2. 计算逾期天数
                days_since_last = calculate_days_since(plant.last_watered)
                overdue = round(days_since_last - dynamic["dynamic_cycle"], 1)

                # 3. 判断是否需要提醒（提前2天开始提醒）
                if overdue >= -2:
                    # 4. 获取浇水质量建议
                    quality_advice = humidity_calc.get_watering_quality_advice(
                        humidity=current_humidity,
                        days_since_last_water=days_since_last,
                        dynamic_cycle=dynamic["dynamic_cycle"]
                    )

                    # 5. 确定紧急程度
                    if overdue >= 0:
                        ratio = overdue / dynamic["dynamic_cycle"] if dynamic["dynamic_cycle"] > 0 else 1
                        if ratio > 0.5:
                            urgency = "high"
                        elif ratio > 0.2:
                            urgency = "medium"
                        else:
                            urgency = "low"
                    else:
                        urgency = "info"

                    # 6. 生成AI文案
                    ai_message = await generate_watering_message(
                        plant_name=plant.nickname,
                        days_overdue=max(0, int(overdue)),
                        humidity=current_humidity,
                        humidity_level=dynamic["humidity"]["level"],
                        recommendation=dynamic["recommendation"],
                        quality_advice=quality_advice
                    )

                    # 计算建议的浇水日期
                    due_date_obj = datetime.now() + timedelta(days=dynamic["dynamic_cycle"])
                    if plant.last_watered:
                        due_date_obj = plant.last_watered + timedelta(days=dynamic["dynamic_cycle"])

                    reminders.append({
                        "plant_id": plant.id,
                        "plant_name": plant.nickname,
                        "type": "water",
                        "message": f"{plant.nickname}{'即将需要浇水' if overdue < 0 else f'已逾期{int(overdue)}天未浇水'}",
                        "ai_message": ai_message,
                        "days_overdue": max(0, int(overdue)),
                        "urgency": urgency,
                        "due_date": due_date_obj.strftime("%Y-%m-%d"),
                        "icon": get_watering_icon(urgency, current_humidity),
                        "dynamic_cycle": dynamic["dynamic_cycle"],
                        "base_cycle": plant.water_cycle,
                        "current_humidity": current_humidity,
                        "humidity_level": dynamic["humidity"]["level"],
                        "adjustment_reason": dynamic["adjustment_reason"],
                        "recommendation": dynamic["recommendation"],
                        "quality_advice": quality_advice
                    })

            # ========== 施肥提醒（保持原逻辑） ==========
            if plant.fertilize_cycle and plant.fertilize_cycle > 0:
                days_since_last = calculate_days_since(plant.last_fertilized)
                overdue = days_since_last - plant.fertilize_cycle

                if overdue >= -1:
                    weather_str = f"{weather_data['weather_text']}，{int(weather_data['temperature'])}℃"
                    ai_message = await generate_smart_message(
                        plant_name=plant.nickname,
                        action="施肥",
                        days_overdue=max(0, overdue),
                        weather=weather_str
                    )

                    last_f = plant.last_fertilized
                    if isinstance(last_f, datetime):
                        last_f = last_f.date()
                    base_date = last_f or date.today()
                    due_date_obj = base_date + timedelta(days=plant.fertilize_cycle)

                    if overdue > 3:
                        urgency = "high"
                    elif overdue > 0:
                        urgency = "medium"
                    else:
                        urgency = "low"

                    reminders.append({
                        "plant_id": plant.id,
                        "plant_name": plant.nickname,
                        "type": "fertilize",
                        "message": f"{plant.nickname}{'即将需要施肥' if overdue < 0 else f'已逾期{overdue}天未施肥'}",
                        "ai_message": ai_message,
                        "days_overdue": max(0, overdue),
                        "urgency": urgency,
                        "due_date": due_date_obj.strftime("%Y-%m-%d"),
                        "icon": get_icon("fertilize", urgency)
                    })

        # 排序：紧急程度高的优先
        urgency_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
        reminders.sort(key=lambda x: (urgency_order.get(x["urgency"], 4), -x["days_overdue"]))

        # 获取湿度级别中文名
        humidity_level_cn = humidity_calc._get_humidity_level_cn(
            humidity_calc.get_humidity_level(current_humidity)
        )

        elapsed = (time.time() - start_time) * 1000
        print(f"✅ 获取提醒列表完成 - {len(reminders)}条提醒, 耗时: {elapsed:.2f}ms")

        return BaseResponse(
            code=200,
            msg="获取成功",
            data={
                "reminders": reminders,
                "total": len(reminders),
                "current_humidity": current_humidity,
                "humidity_level": humidity_level_cn
            }
        )

    except Exception as e:
        print(f"获取提醒列表失败: {e}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            msg=f"获取提醒失败: {str(e)}",
            data=None
        )


@router.post("/plants/{plant_id}/water", response_model=BaseResponse)
async def record_watering(plant_id: int, current_user: User = Depends(get_current_user)):
    """浇水打卡"""
    plant = await Plant.get_or_none(id=plant_id, user=current_user, is_deleted=False)
    if not plant:
        return BaseResponse(code=404, msg="植物不存在或无权操作")
    plant.last_watered = date.today()
    await plant.save()
    return BaseResponse(
        code=200,
        msg="浇水打卡成功",
        data=PlantOperationResponse(
            plant_id=plant.id,
            operation="water",
            operated_at=str(plant.last_watered)
        ).model_dump()
    )


@router.post("/plants/{plant_id}/fertilize", response_model=BaseResponse)
async def record_fertilizing(plant_id: int, current_user: User = Depends(get_current_user)):
    """施肥打卡"""
    plant = await Plant.get_or_none(id=plant_id, user=current_user, is_deleted=False)
    if not plant:
        return BaseResponse(code=404, msg="植物不存在或无权操作")
    plant.last_fertilized = date.today()
    await plant.save()
    return BaseResponse(
        code=200,
        msg="施肥打卡成功",
        data=PlantOperationResponse(
            plant_id=plant.id,
            operation="fertilize",
            operated_at=str(plant.last_fertilized)
        ).model_dump()
    )


@router.post("/plants/recommend", response_model=BaseResponse)
async def recommend_plant_cycles(
        req: PlantRecommendationReq,
        current_user: User = Depends(get_current_user)
):
    """根据植物品种获取 AI 推荐的养护周期"""
    if not req.species or req.species == "其他":
        return BaseResponse(code=200, msg="默认值", data={"water_cycle": 7, "fertilize_cycle": 30})

    recommendation = await get_plant_recommendation_from_ai(req.species)
    return BaseResponse(code=200, msg="获取建议成功", data=recommendation)


@router.delete("/plants/{plant_id}", response_model=BaseResponse)
async def delete_plant(
        plant_id: int,
        current_user: User = Depends(get_current_user)
):
    """删除植物（软删除）- 同时删除关联日记"""
    plant = await Plant.get_or_none(
        id=plant_id,
        user=current_user,
        is_deleted=False
    )
    if not plant:
        return BaseResponse(code=404, msg="植物不存在")

    plant.is_deleted = True
    await plant.save()

    await Diary.filter(plant_id=plant_id).update(is_deleted=True)

    return BaseResponse(code=200, msg="植物删除成功")