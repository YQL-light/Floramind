# app/api/v1/endpoints/plant.py
# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Form, Request
from fastapi.responses import JSONResponse
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import aiohttp
import json

# 创建 Router 实例
router = APIRouter()

# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = "sk-17a01a6a51624698ba06dfdec42bec78"

# 植物养护专家系统提示词
PLANT_EXPERT_SYSTEM_PROMPT = """你是一个专业的植物养护专家，专注于室内植物、多肉植物、观叶植物的养护指导。请遵循以下原则：
1. 提供专业、准确的植物养护建议
2. 回答要具体、实用，避免笼统
3. 针对用户的具体问题给出针对性解决方案
4. 如果涉及病虫害，要说明识别方法和具体治疗步骤
5. 浇水建议要具体到频率、水量和注意事项
6. 光照建议要说明具体的光照时长和强度
7. 施肥建议要说明肥料类型、频率和用量
8. 如果用户提供了植物图片，请分析图片中的植物状态并提供养护建议

请用中文回答，语气亲切专业，像一位经验丰富的园艺师。如果用户的问题信息不足，请主动询问更多细节以便给出更精准的建议。"""

# 模拟知识库数据
KNOWLEDGE_BASE = [
    {
        "id": "1",
        "title": "绿萝养护指南",
        "content": "绿萝是一种常见的室内观叶植物，适合初学者养护。\n\n**养护要点：**\n1. 光照：喜欢明亮的散射光，避免阳光直射\n2. 浇水：春夏每周浇水1-2次，冬季减少到10天一次\n3. 温度：适宜温度18-25℃，冬季不低于10℃\n4. 施肥：春夏每月施一次稀释的液体肥料",
        "category": "观叶植物",
        "tags": ["室内", "易养", "净化空气"]
    },
    {
        "id": "2",
        "title": "多肉植物浇水技巧",
        "content": "多肉植物浇水要遵循\"宁干勿湿\"的原则。\n\n**浇水技巧：**\n1. 判断方法：手指插入土壤2-3厘米，干燥后再浇水\n2. 浇水时间：春秋季节生长期，土干透后浇透水\n3. 夏季养护：减少浇水，注意通风，避免高温高湿\n4. 冬季养护：保持土壤干燥，每月少量浇水或不浇水",
        "category": "多肉植物",
        "tags": ["浇水", "耐旱", "养护技巧"]
    },
    {
        "id": "3",
        "title": "植物叶片发黄原因分析",
        "content": "植物叶片发黄是常见问题，可能的原因有：\n\n**常见原因及解决方法：**\n1. 浇水过多：减少浇水频率，改善排水\n2. 光照不足：移到明亮处，但避免阳光直射\n3. 营养不足：定期施肥，使用平衡型肥料\n4. 病虫害：检查叶片背面，使用相应药物治疗",
        "category": "问题诊断",
        "tags": ["叶片发黄", "诊断", "治疗"]
    }
]

# 存储对话历史
conversations_db = {}


# 健康检查接口
@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "植物养护AI助手后端运行正常", "timestamp": datetime.now().isoformat()}


# 增强版对话接口（仅支持文字）
@router.post("/chat")
async def chat_with_ai(
        request: Request,
        message: str = Form(""),  # 默认值为空字符串
        conversation_id: Optional[str] = Form(None)
):
    try:
        # 检查是否有内容
        if not message.strip():
            raise HTTPException(status_code=400, detail="请提供问题")

        # 处理对话ID
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # 获取或创建对话历史
        if conversation_id not in conversations_db:
            # 创建对话标题
            if message and len(message) > 20:
                title = message[:20] + "..."
            elif message:
                title = message
            else:
                title = "植物咨询"

            conversations_db[conversation_id] = {
                "id": conversation_id,
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "title": title
            }

        # 获取对话历史
        history_messages = []
        if conversation_id in conversations_db:
            history_messages = conversations_db[conversation_id]["messages"]

        # 构建当前用户消息文本
        message_text = message.strip() if message else ""

        # 构建DeepSeek API请求消息 - 纯文本格式
        messages_for_api = [
            {
                "role": "system",
                "content": PLANT_EXPERT_SYSTEM_PROMPT
            }
        ]

        # 添加历史消息
        for msg in history_messages[-6:]:
            messages_for_api.append({
                "role": msg["role"],
                "content": msg.get("content", "")
            })

        # 添加当前用户消息
        messages_for_api.append({
            "role": "user",
            "content": message_text
        })

        # 调用DeepSeek API
        ai_response = "抱歉，暂时无法获取AI回复，请稍后重试。"
        result = {}

        if DEEPSEEK_API_KEY:
            try:
                # 仅使用文本模型
                model_to_use = "deepseek-chat"

                # 构建请求体
                payload = {
                    "model": model_to_use,
                    "messages": messages_for_api,
                    "max_tokens": 2000,
                    "temperature": 0.7,
                    "stream": False
                }

                headers = {
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                            DEEPSEEK_API_URL,
                            json=payload,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:

                        if response.status != 200:
                            error_text = await response.text()
                            print(f"DeepSeek API错误: {error_text}")

                            # 尝试解析错误信息
                            try:
                                error_data = json.loads(error_text)
                                error_message = error_data.get("error", {}).get("message", error_text)
                                print(f"解析后的错误信息: {error_message}")
                                ai_response = f"AI服务暂时不可用：{error_message[:100]}"
                            except:
                                ai_response = "抱歉，服务遇到了一些问题，请稍后重试。"
                        else:
                            # 解析响应
                            response_data = await response.json()
                            print(f"DeepSeek响应解析成功")

                            # 提取AI回复
                            try:
                                ai_response = response_data.get("choices", [{}])[0].get("message", {}).get("content",
                                                                                                           "")
                                if not ai_response:
                                    ai_response = "抱歉，未能获取到有效的回复，请稍后再试。"
                            except Exception as e:
                                print(f"解析AI回复失败: {str(e)}")
                                ai_response = "抱歉，数据解析错误。"

                            result = {
                                "usage": response_data.get("usage", {}),
                                "model": response_data.get("model", "")
                            }
            except aiohttp.ClientError as e:
                print(f"网络请求错误: {str(e)}")
                ai_response = "网络连接出现问题，请检查网络后重试。"
            except Exception as e:
                print(f"调用DeepSeek API失败: {str(e)}")
                import traceback
                traceback.print_exc()
                ai_response = "AI服务暂时不可用，请稍后再试。"
        else:
            print("警告：DeepSeek API密钥未配置")
            ai_response = "请配置API Key以使用AI助手功能。"

        # 保存对话记录
        conversations_db[conversation_id]["messages"].extend([
            {"role": "user", "content": message_text},
            {"role": "assistant", "content": ai_response}
        ])

        print(f"对话已保存，总消息数: {len(conversations_db[conversation_id]['messages'])}")

        # 构建响应
        response_dict = {
            "success": True,
            "message": ai_response,
            "conversation_id": conversation_id,
            "usage": result.get("usage", {})
        }

        return JSONResponse(
            content=response_dict,
            media_type="application/json; charset=utf-8",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )

    except HTTPException as he:
        print(f"HTTP异常: {he.detail}")
        raise he
    except Exception as e:
        print(f"处理聊天请求时发生未知错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")


# 知识库接口
@router.get("/knowledge")
async def get_knowledge_base():
    """获取知识库列表"""
    return {
        "success": True,
        "knowledge": KNOWLEDGE_BASE
    }


@router.get("/knowledge/{knowledge_id}")
async def get_knowledge_detail(knowledge_id: str):
    """获取知识库详情"""
    for item in KNOWLEDGE_BASE:
        if item["id"] == knowledge_id:
            return item
    raise HTTPException(status_code=404, detail="知识库条目不存在")


# 获取对话历史
@router.get("/conversations")
async def get_conversation_history():
    """获取对话历史列表"""
    # 返回最近的10个对话
    recent_conversations = list(conversations_db.values())[-10:]

    for conv in recent_conversations:
        # 只返回基本信息，不包含完整消息历史
        conv["message_count"] = len(conv["messages"]) // 2

        if conv["messages"]:
            last_msg = conv["messages"][-1]["content"]
            if len(last_msg) > 50:
                conv["last_message"] = last_msg[:50] + "..."
            else:
                conv["last_message"] = last_msg
        else:
            conv["last_message"] = ""

    return {"conversations": recent_conversations}


# 获取特定对话详情
@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: str):
    """获取特定对话的详细信息"""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="对话不存在")

    return conversations_db[conversation_id]