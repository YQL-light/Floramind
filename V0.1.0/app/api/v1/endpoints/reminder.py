# app/api/v1/endpoints/reminder.py
import json
import re
from fastapi import APIRouter, Depends, HTTPException,UploadFile, File
from datetime import date, timedelta, datetime
from pydantic import BaseModel
from typing import List, Optional
import aiohttp
import asyncio
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
# 请将你的 DeepSeek Key 放在这里或环境变量中
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = "sk-17a01a6a51624698ba06dfdec42bec78"

# OpenWeatherMap 配置 (建议申请一个免费Key，或者使用代码下方的模拟模式)
WEATHER_API_KEY = "d7aadb72af4007994d98593361db009b"
WEATHER_BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# 配置上传目录
UPLOAD_DIR = "uploads"
PLANT_AVATAR_DIR_NAME = "plantAvatars"
# 完整物理路径: uploads/plantAvatars
PLANT_AVATAR_FULL_DIR = os.path.join(UPLOAD_DIR, PLANT_AVATAR_DIR_NAME)
# 默认头像路径 (相对 uploads)
DEFAULT_PLANT_AVATAR = f"{PLANT_AVATAR_DIR_NAME}/default_avatar.png"

# 确保目录存在
os.makedirs(PLANT_AVATAR_FULL_DIR, exist_ok=True)

# --- 辅助函数 ---

def calculate_days_overdue(last_date: Optional[object], cycle: int) -> int:
    if not last_date: return 999
    if isinstance(last_date, datetime):
        last_date_obj = last_date.date()
    elif isinstance(last_date, date):
        last_date_obj = last_date
    else:
        return 999
    today = date.today()
    days_passed = (today - last_date_obj).days
    return days_passed - cycle


def get_urgency_level(days_overdue: int, cycle: int) -> str:
    if days_overdue < 0: return "low"
    safe_cycle = cycle if cycle > 0 else 1
    ratio = days_overdue / safe_cycle
    if ratio > 0.5: return "high"
    if ratio > 0.2: return "medium"
    return "low"


def get_icon(operation_type: str, urgency: str) -> str:
    base_icons = {"water": "💧", "fertilize": "🌱"}
    base = base_icons.get(operation_type, "🍃")
    if urgency == "high": return f"{base}🔥"
    if urgency == "medium": return f"{base}⏰"
    return base


async def translate_city_llm(city_name: str) -> str:
    """
    使用 LLM 将中文城市名转换为英文/拼音
    """
    print(f"正在调用 LLM 翻译城市名: {city_name} ...")

    # 2. 调用 LLM
    system_prompt = (
        "你是一个专业的地理翻译助手。请将用户输入的中文城市名称转换为用于 "
        "OpenWeatherMap API 的标准英文名称（通常是拼音）。"
        "要求：只返回英文名称，不要包含任何标点符号、解释或额外文本。"
        "例如：输入'北京'，返回'Beijing'；输入'西安'，返回'Xian'。"
        "确保不要返回任何标点符号和其他文件，只要单纯返回城市英文名"
    )

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": city_name}
                ],
                "temperature": 0.1,  # 低温度以保证准确性
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
                # 清理可能产生的额外符号
                english_name = re.sub(r'[^\w\s]', '', english_name)
                print(f"LLM翻译城市名为：{english_name}")
                return english_name
            else:
                print(f"LLM 翻译失败: {response.status_code} - {response.text}")
                return city_name  # 失败则返回原名尝试

    except Exception as e:
        print(f"LLM 调用异常: {e}")
        return city_name

# --- 新增：天气获取函数 ---
async def get_current_weather(city: str) -> str:

    if not city:
        return "未知天气"

    api_city = await translate_city_llm(city)

    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "q": api_city,
                "appid": WEATHER_API_KEY,
                "units": "metric",  # 摄氏度
                "lang": "zh_cn"  # 中文返回
            }
            async with session.get(WEATHER_BASE_URL, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    desc = data["weather"][0]["description"]
                    temp = round(data["main"]["temp"])
                    return f"{desc}，{temp}℃"
    except Exception as e:
        print(f"天气获取失败: {e}")

    return "天气数据暂时不可用"


# --- 新增：AI 生成拟人化提醒文案 ---
async def generate_smart_message(plant_name: str, action: str, days_overdue: int, weather: str) -> str:
    """
    调用 DeepSeek 生成植物拟人化吐槽
    """

    system_prompt = """
    你是一个可爱体贴、有时候有点小脾气的植物小精灵。
    请根据植物种类、缺水/缺肥天数以及当前天气，生成一小段简短的提醒（50字左右）。
    语气要求：
    1. 使用第一人称“我”。
    2. 如果逾期天数很长（>7天），语气要委屈或生气。
    3. 如果逾期天数短（<3天），语气要可爱、期待。
    4. 适当结合天气情况（包括气温等，例如：天热要多喝水，天冷要保暖）。
    5. 要拟人化、可爱，可以适当添加emoji。
    6. 可以根据植物的习性转化为性格，体现在提醒中，使得提醒具有个性。
    7. 如果遇到不认识的植物，可以不突出个性，只要可爱拟人即可。
    """

    user_prompt = f"""我是{plant_name}。
    状态：已经逾期{days_overdue}天没有{action}了。
    外面天气：{weather}。
    请对主人说一段话："""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": 100,  # 限制长度
                "temperature": 0.8
            }
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            async with session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    ai_text = result["choices"][0]["message"]["content"].strip()
                    # 去掉可能的引号
                    return ai_text.replace('"', '').replace("'", "")
    except Exception as e:
        print(f"AI 生成失败: {e}")


# --- 新增：AI 获取植物养护建议 ---
async def get_plant_recommendation_from_ai(species: str) -> dict:
    """
    询问 AI 该植物的浇水和施肥周期
    """
    system_prompt = """
    你是一个专业的植物养护专家。
    请根据用户提供的植物品种，推荐合理的“浇水周期（天）”和“施肥周期（天）”。

    要求：
    1. 必须返回纯 JSON 格式。
    2. JSON 格式必须包含两个字段：`water_cycle` (整数) 和 `fertilize_cycle` (整数)。
    3. 不要包含任何 markdown 格式（如 ```json），只返回 JSON 字符串。
    4. 如果植物品种不明确，给出一个保守的默认值（如浇水7天，施肥30天）。
    """

    user_prompt = f"植物种类：{species},植物"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.5,  # 降低随机性，获取较稳定的建议
                "max_tokens": 50
            }
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            async with session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    content = result["choices"][0]["message"]["content"].strip()
                    # 清理可能存在的 markdown 符号
                    content = content.replace("```json", "").replace("```", "").strip()
                    return json.loads(content)
    except Exception as e:
        print(f"AI 推荐失败: {e}")

    # 失败时的默认值
    return {"water_cycle": 7, "fertilize_cycle": 30}

def build_avatar_url(avatar_path: Optional[str]) -> str:
    """
    返回可访问的植物头像 URL。
    假设 static 目录挂载在 /uploads 下。
    """
    path = avatar_path or DEFAULT_PLANT_AVATAR
    if path.startswith("http"):
        return path
    # 统一格式，确保前端能访问到 (根据你的静态文件配置)
    return f"/uploads/{path}"

# --- 路由定义 ---

@router.get("/get_plants", response_model=BaseResponse)
async def get_user_plants(current_user: User = Depends(get_current_user)):
    """获取用户所有植物"""
    plants = await Plant.filter(user=current_user, is_deleted=False).order_by("-created_at").all()
    plant_data = [PlantOut.model_validate(p) for p in plants]
    return BaseResponse(code=200, msg="获取成功", data=plant_data)

# ---------------------------------------------------------
# 1. 独立上传接口 (使用 UploadFile)
# 前端先调用这个接口上传图片，拿到返回的 url
# ---------------------------------------------------------
@router.post("/upload_avatar", response_model=BaseResponse)
async def upload_plant_avatar(
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_user)
):
    """
    第一步：上传图片
    Content-Type: multipart/form-data
    返回: {"url": "plantAvatars/xxxx.jpg"}
    """
    # 检查文件类型
    if not file.content_type.startswith('image/'):
        return BaseResponse(code=400, msg="请上传图片文件")

    # 检查文件大小 (需读取流)
    # 注意：UploadFile 是流式上传，读取后指针会到末尾，如果需要保存需 seek(0) 或直接写入
    # 这里简单判断不做严格大小限制，或者在 nginx 层做限制，Python 层做流拷贝

    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    unique_name = f"plant_{uuid.uuid4().hex}{file_ext}"
    file_save_path = os.path.join(PLANT_AVATAR_FULL_DIR, unique_name)

    # 相对数据库路径
    db_path = f"{PLANT_AVATAR_DIR_NAME}/{unique_name}"

    try:
        with open(file_save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return BaseResponse(
            msg="图片上传成功",
            data={"url": db_path}  # 返回给前端，前端下次请求带上这个
        )
    except Exception as e:
        return BaseResponse(code=500, msg=f"上传失败: {str(e)}")


# ---------------------------------------------------------
# 2. 创建植物接口 (使用纯 JSON)
# 前端将上一步拿到的 url 填入 plantAvatar_url 字段
# ---------------------------------------------------------
@router.post("/plants", response_model=BaseResponse)
async def create_plant(
        plant_in: PlantCreate,  # 直接接收 JSON Body
        current_user: User = Depends(get_current_user)
):
    """
    第二步：提交植物信息
    Content-Type: application/json
    Body: {
        "nickname": "...",
        "plantAvatar_url": "plantAvatars/xxxx.jpg" (来自第一步的返回值)
    }
    """

    # 处理日期
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

    # 使用前端传来的图片路径，如果没有则用默认
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
        msg="植物添加成功",
        data={
            "plant_id": plant.id,
            "nickname": plant.nickname,
            "plantAvatar_url": build_avatar_url(plant.plantAvatar_url)
        }
    )
# -------------------------------------------------------------
# 核心修改：改造 get_reminders 接口，集成 AI 和 天气
# -------------------------------------------------------------
@router.get("/reminders", response_model=BaseResponse)
async def get_reminders(current_user: User = Depends(get_current_user)):
    """
    获取智能提醒列表（集成AI拟人化提醒 + 实时天气）
    """
    plants = await Plant.filter(user=current_user, is_deleted=False).all()
    today = date.today()

    # 1. 获取用户城市天气 (默认取 user 表中的 city，若无则默认 "Beijing")
    user_city = current_user.location_city or "北京"
    weather_info = await get_current_weather(user_city)

    reminders: List[ReminderItem] = []

    # 需要调用 AI 生成的任务列表
    ai_tasks = []

    for plant in plants:
        # --- 浇水逻辑 ---
        if plant.water_cycle > 0:
            overdue = calculate_days_overdue(plant.last_watered, plant.water_cycle)
            # 只有当 需要浇水 (overdue >= -1) 时才生成提醒
            if overdue >= -1:
                urgency = get_urgency_level(max(0, overdue), plant.water_cycle)
                last_w = plant.last_watered
                if isinstance(last_w, datetime): last_w = last_w.date()
                base_date = last_w or today
                due_date_obj = base_date + timedelta(days=plant.water_cycle)
                standard_msg = f"{plant.nickname}明天需要浇水" if overdue == -1 else f"{plant.nickname}已逾期{overdue}天未浇水"

                ai_tasks.append({
                    "plant": plant,
                    "type": "water",
                    "action_name": "浇水",
                    "overdue": overdue,
                    "urgency": urgency,
                    "due_date": due_date_obj,
                    "standard_msg": standard_msg  # <--- 将标准标题存入任务参数
                })

        # --- 施肥逻辑 ---
        if plant.fertilize_cycle > 0:
            overdue = calculate_days_overdue(plant.last_fertilized, plant.fertilize_cycle)
            if overdue >= -1:
                urgency = get_urgency_level(max(0, overdue), plant.fertilize_cycle)
                last_f = plant.last_fertilized
                if isinstance(last_f, datetime): last_f = last_f.date()
                base_date = last_f or today
                due_date_obj = base_date + timedelta(days=plant.fertilize_cycle)
                standard_msg = f"{plant.nickname}明天需要施肥" if overdue == -1 else f"{plant.nickname}已逾期{overdue}天未施肥"

                ai_tasks.append({
                    "plant": plant,
                    "type": "fertilize",
                    "action_name": "施肥",
                    "overdue": overdue,
                    "urgency": urgency,
                    "due_date": due_date_obj,
                    "standard_msg": standard_msg  # <--- 将标准标题存入任务参数
                })

    # 2. 并发执行 AI 生成任务 (极大地提高速度)
    # 如果植物很多，串行调用 AI 会导致接口响应非常慢，必须用 asyncio.gather
    async def process_reminder_task(task):
        # 调用 AI 生成文案
        ai_text = await generate_smart_message(
            plant_name=task["plant"].nickname,
            action=task["action_name"],
            days_overdue=max(0, task["overdue"]),
            weather=weather_info
        )

        return ReminderItem(
            plant_id=task["plant"].id,
            plant_name=task["plant"].nickname,
            type=task["type"],
            message=task["standard_msg"],  # <--- 这里放标准标题
            ai_message=ai_text,  # <--- 这里放 AI 文案
            days_overdue=max(0, task["overdue"]),
            urgency=task["urgency"],
            due_date=task["due_date"].strftime("%Y-%m-%d"),
            icon=get_icon(task["type"], task["urgency"])
        )

    # 限制 AI 并发数量 (比如最多同时生成 5 条，防止 API 限流)
    # 对于 MVP，我们可以直接全部并发，或者只取最紧急的 Top 3 调用 AI，其他的用普通文案
    # 这里演示全部并发:
    if ai_tasks:
        generated_reminders = await asyncio.gather(*[process_reminder_task(t) for t in ai_tasks])
        reminders.extend(generated_reminders)

    # 3. 排序
    urgency_map = {"high": 0, "medium": 1, "low": 2}
    reminders.sort(key=lambda x: (urgency_map[x.urgency], -x.days_overdue))

    return BaseResponse(data=ReminderListResponse(reminders=reminders, total=len(reminders)).model_dump())


@router.post("/plants/{plant_id}/water", response_model=BaseResponse)
async def record_watering(plant_id: int, current_user: User = Depends(get_current_user)):
    plant = await Plant.get_or_none(id=plant_id, user=current_user, is_deleted=False)
    if not plant: return BaseResponse(code=404, msg="植物不存在或无权操作")
    plant.last_watered = date.today()
    await plant.save()
    return BaseResponse(msg="浇水打卡成功", data=PlantOperationResponse(plant_id=plant.id, operation="water",
                                                                        operated_at=str(plant.last_watered)).dict())


@router.post("/plants/{plant_id}/fertilize", response_model=BaseResponse)
async def record_fertilizing(plant_id: int, current_user: User = Depends(get_current_user)):
    plant = await Plant.get_or_none(id=plant_id, user=current_user, is_deleted=False)
    if not plant: return BaseResponse(code=404, msg="植物不存在或无权操作")
    plant.last_fertilized = date.today()
    await plant.save()
    return BaseResponse(msg="施肥打卡成功", data=PlantOperationResponse(plant_id=plant.id, operation="fertilize",
                                                                        operated_at=str(plant.last_fertilized)).model_dump())

@router.post("/plants/recommend", response_model=BaseResponse)
async def recommend_plant_cycles(
        req: PlantRecommendationReq,
        current_user: User = Depends(get_current_user)
):
    """
    根据植物品种获取 AI 推荐的养护周期
    """
    if not req.species or req.species == "其他":
        return BaseResponse(code=200, msg="默认值", data={"water_cycle": 7, "fertilize_cycle": 30})

    recommendation = await get_plant_recommendation_from_ai(req.species)
    return BaseResponse(code=200, msg="获取建议成功", data=recommendation)