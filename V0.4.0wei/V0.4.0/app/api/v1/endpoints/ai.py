# app/api/v1/endpoints/ai.py
# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import StreamingResponse
import uuid
from datetime import datetime, timedelta
from typing import Optional
import aiohttp
import json
import asyncio

router = APIRouter()

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = "sk-17a01a6a51624698ba06dfdec42bec78"

PLANT_EXPERT_SYSTEM_PROMPT = """你是一个专业的植物养护专家，专注于室内植物、多肉植物、观叶植物的养护指导。请遵循以下原则：
1. 提供专业、准确的植物养护建议
2. 回答要具体、实用，避免笼统
3. 针对用户的具体问题给出针对性解决方案
4. 如果涉及病虫害，要说明识别方法和具体治疗步骤
5. 浇水建议要具体到频率、水量和注意事项
6. 光照建议要说明具体的光照时长和强度
7. 施肥建议要说明肥料类型、频率和用量
8. 如果用户提供了植物图片，请分析图片中的植物状态并提供养护建议
9. 每次回答在100字左右

请用中文回答，语气亲切专业，像一位经验丰富的园艺师。如果用户的问题信息不足，请主动询问更多细节以便给出更精准的建议。"""

conversations_db = {}
CACHE_TTL = 3600
memory_cache = {}

def get_cache_key(message: str) -> str:
    return message.strip().lower()[:200]

def get_cached_response(key: str) -> Optional[str]:
    if key in memory_cache:
        t, r = memory_cache[key]
        if datetime.now() - t < timedelta(seconds=CACHE_TTL):
            return r
    return None

def set_cached_response(key: str, response: str):
    memory_cache[key] = (datetime.now(), response)

# 普通聊天接口
@router.post("/chat")
async def chat_with_ai(
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None)
):
    try:
        if not message.strip():
            raise HTTPException(status_code=400, detail="请输入问题")

        cache_key = get_cache_key(message)
        cached = get_cached_response(cache_key)
        if cached:
            return {"success": True, "message": cached, "conversation_id": conversation_id or str(uuid.uuid4()), "from_cache": True}

        cid = conversation_id or str(uuid.uuid4())
        if cid not in conversations_db:
            conversations_db[cid] = {"id": cid, "messages": [], "title": message[:20] + "..."}

        messages = [{"role": "system", "content": PLANT_EXPERT_SYSTEM_PROMPT}]
        for m in conversations_db[cid]["messages"][-6:]:
            messages.append({"role": m["role"], "content": m.get("content", "")})
        messages.append({"role": "user", "content": message.strip()})

        resp = ""
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": 1500,
            "temperature": 0.7,
            "stream": False
        }
        headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=45)) as s:
            async with s.post(DEEPSEEK_API_URL, json=payload, headers=headers) as r:
                if r.status == 200:
                    data = await r.json()
                    resp = data["choices"][0]["message"]["content"]
                    set_cached_response(cache_key, resp)

        conversations_db[cid]["messages"].append({"role": "user", "content": message.strip()})
        conversations_db[cid]["messages"].append({"role": "assistant", "content": resp})
        return {"success": True, "message": resp, "conversation_id": cid}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ 流式 SSE 接口（最终完美版）
@router.post("/stream")
async def stream_chat(
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None)
):
    async def gen():
        try:
            cid = conversation_id or str(uuid.uuid4())
            if cid not in conversations_db:
                conversations_db[cid] = {"id": cid, "messages": [], "title": message[:20] + "..."}

            messages = [{"role": "system", "content": PLANT_EXPERT_SYSTEM_PROMPT}]
            for m in conversations_db[cid]["messages"][-6:]:
                messages.append({"role": m["role"], "content": m.get("content", "")})
            messages.append({"role": "user", "content": message.strip()})

            full = ""
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "stream": True,
                "max_tokens": 1500,
                "temperature": 0.7
            }
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
                async with session.post(DEEPSEEK_API_URL, json=payload, headers=headers) as resp:
                    async for line in resp.content:
                        try:
                            line = line.decode("utf-8").strip()
                            if not line.startswith("data:"):
                                continue
                            if "[DONE]" in line:
                                break
                            raw = line[5:].strip()
                            data = json.loads(raw)
                            token = data["choices"][0]["delta"].get("content", "")
                            if not token:
                                continue
                            full += token
                            yield f"data: {json.dumps({'message': token}, ensure_ascii=False)}\n\n"
                            await asyncio.sleep(0.01)
                        except:
                            continue

            conversations_db[cid]["messages"].append({"role": "user", "content": message.strip()})
            conversations_db[cid]["messages"].append({"role": "assistant", "content": full})
            set_cached_response(get_cache_key(message), full)
            yield f"data: {json.dumps({'message':'[DONE]'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'message':'出错'})}\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )