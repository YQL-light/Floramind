from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from app.schemas.user import BaseResponse


# 创建日记的请求参数（完全对应前端表单）
class DiaryCreate(BaseModel):
    plantId: str  # 植物ID（前端是字符串）
    title: Optional[str] = None
    content: str  # 日记内容
    activityType: Optional[str] = ""  # 活动类型
    weather: Optional[str] = "sunny"  # 天气
    temperature: Optional[str] = ""  # 温度范围
    photos: Optional[List[str]] = []  # 图片URL列表
    date: Optional[str] = None  # 日记日期，格式：YYYY-MM-DD


# 更新日记的请求参数
class DiaryUpdate(BaseModel):
    plantId: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    activityType: Optional[str] = None
    weather: Optional[str] = None
    temperature: Optional[str] = None
    photos: Optional[List[str]] = None
    date: Optional[str] = None


# 单篇日记响应（完全对应前端结构）
class DiaryItem(BaseModel):
    id: str  # 字符串ID
    plantId: str  # 植物ID
    plantNickname: Optional[str] = None  # 植物昵称
    plantImageUrl: Optional[str] = None  # 植物图片
    title: Optional[str] = None
    content: str
    activityType: Optional[str] = ""
    weather: Optional[str] = "sunny"
    temperature: Optional[str] = ""
    photos: List[str] = []
    date: str  # 格式：YYYY-MM-DD
    createdAt: Optional[str] = None

    class Config:
        from_attributes = True


# 日记列表响应（对应前端diaryData）
class DiaryListData(BaseModel):
    diaries: List[DiaryItem]
    total: int
    plants: Optional[List] = None  # 植物列表，用于筛选


# 日记API响应包装
class DiaryResponse(BaseResponse):
    """日记模块专用的API响应"""
    data: Optional[DiaryListData] = None

    @classmethod
    def success(cls, diaries: List[DiaryItem], total: int, plants: Optional[List] = None):
        return cls(
            code=200,
            msg="success",
            data=DiaryListData(
                diaries=diaries,
                total=total,
                plants=plants
            )
        )


# 单个日记操作响应
class DiaryOperationData(BaseModel):
    diaryId: str
    operation: str  # "create", "update", "delete"
    success: bool = True
    message: str = "操作成功"


class DiaryOperationResponse(BaseResponse):
    data: Optional[DiaryOperationData] = None

    @classmethod
    def success(cls, diary_id: str, operation: str, message: str = "操作成功"):
        return cls(
            code=200,
            msg=message,
            data=DiaryOperationData(
                diaryId=diary_id,
                operation=operation,
                message=message
            )
        )


# 植物基本信息（用于筛选）
class PlantFilterItem(BaseModel):
    id: str
    nickname: str
    imageUrl: Optional[str] = None

    class Config:
        from_attributes = True