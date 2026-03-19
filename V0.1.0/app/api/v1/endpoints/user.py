from fastapi import APIRouter
# 【修改 1】引入 ResetPasswordRequest
from app.schemas.user import UserRegister, BaseResponse, UserLogin, ResetPasswordRequest
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter()


# --------------------------
# 注册接口 (无验证码)
# --------------------------
@router.post("/register", response_model=BaseResponse)
async def register(req: UserRegister):
    # 1. 检查用户名是否已存在
    if await User.filter(username=req.username).exists():
        return BaseResponse(code=400, msg="用户名已存在")

    # 2. 检查邮箱是否已存在
    if await User.filter(email=req.email).exists():
        return BaseResponse(code=400, msg="该邮箱已被注册")

    # 3. 创建用户 (密码加密存储)
    # 【修改 2】这里加入了 security_answer 字段的保存
    new_user = await User.create(
        username=req.username,
        email=req.email,
        password=get_password_hash(req.password),
        security_answer=req.security_answer,  # 保存密保答案
        location_city = req.location_city
    )

    return BaseResponse(
        msg="注册成功",
        data={"user_id": new_user.id, "username": new_user.username}
    )


@router.post("/login", response_model=BaseResponse)
async def login(user_in: UserLogin):
    """
    用户登录 (JSON 方式)
    """
    # 1. 查找用户
    user = await User.get_or_none(username=user_in.account)
    if not user:
        user = await User.get_or_none(email=user_in.account)

    # 2. 验证
    if not user or not verify_password(user_in.password, user.password):
        return BaseResponse(code=400, msg="账号或密码错误")

    # 3. 生成 Token
    access_token = create_access_token(subject=user.id)

    # 4. 返回结果
    return BaseResponse(
        code=200,
        msg="登录成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }
    )


# --------------------------
# 【新增】重置密码接口
# --------------------------
@router.post("/reset-password", response_model=BaseResponse)
async def reset_password(req: ResetPasswordRequest):
    """
    通过密保问题重置密码
    """
    # 1. 查找用户 (支持 用户名 或 邮箱)
    user = await User.get_or_none(username=req.account)
    if not user:
        user = await User.get_or_none(email=req.account)

    if not user:
        return BaseResponse(code=400, msg="该账号不存在")

    # 2. 检查用户是否设置了密保
    if not user.security_answer:
        return BaseResponse(code=400, msg="该账号未设置密保问题，无法自助找回")

    # 3. 验证密保答案 (去除首尾空格后比较)
    if user.security_answer.strip() != req.security_answer.strip():
        return BaseResponse(code=400, msg="密保答案错误，验证失败")

    # 4. 更新密码 (加密存储)
    user.password = get_password_hash(req.new_password)
    await user.save()

    return BaseResponse(code=200, msg="密码重置成功，请使用新密码登录")