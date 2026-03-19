# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional, Any

# 基础响应结构
class BaseResponse(BaseModel):
    code: int = 200
    msg: str = "success"
    data: Optional[Any] = None

# 注册请求参数
class UserRegister(BaseModel):
    username: str
    email: EmailStr # 数据库要求Email非空，这里必须传
    password: str
    security_answer: str
    location_city: Optional[str] = None

# 登录请求参数
class UserLogin(BaseModel):
    # 允许使用 用户名 或 邮箱 登录
    account: str
    password: str

# Token返回数据
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str

# 新增重置密码请求参数
class ResetPasswordRequest(BaseModel):
    account: str         # 用户名或邮箱
    security_answer: str # 密保答案
    new_password: str    # 新密码
