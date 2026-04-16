# app/schemas/user_center.py
from pydantic import BaseModel
from typing import Optional


# 用户资料响应
class UserProfile(BaseModel):
    nickname: str  # 使用 username 作为昵称
    phone: Optional[str] = None
    avatar: Optional[str] = None  # avatar_url
    signature: Optional[str] = None  # 个性签名，可以存储在 notification_preferences 或其他字段

# 更新用户资料请求
class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    signature: Optional[str] = None

# 修改密码请求
class PasswordChange(BaseModel):
    oldPassword: str
    newPassword: str

# 统计数据响应
class UserStats(BaseModel):
    plantCount: int
    diaryCount: int
    careDays: int
