from fastapi import APIRouter, Depends, UploadFile, File
import os
import uuid
from datetime import date

from app.api.deps import get_current_user
from app.models.user import User
from app.models.plant import Plant
from app.models.diary import Diary
from app.schemas.user import BaseResponse
from app.schemas.user_center import (
    UserProfile,
    UserProfileUpdate,
    PasswordChange,
    UserStats,
)
from app.core.security import verify_password, get_password_hash

router = APIRouter()

# 确保 uploads 目录存在
os.makedirs("uploads/avatars", exist_ok=True)


@router.get("/profile", response_model=BaseResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    获取当前用户的个人资料
    """
    # 从 notification_preferences 中获取 signature（如果存在）
    signature = None
    if current_user.notification_preferences and isinstance(current_user.notification_preferences, dict):
        signature = current_user.notification_preferences.get("signature")
    
    # 构建头像 URL
    avatar_url = None
    if current_user.avatar_url:
        # 如果 avatar_url 是相对路径，添加 /uploads 前缀
        if not current_user.avatar_url.startswith("http"):
            avatar_url = f"/uploads/{current_user.avatar_url}"
        else:
            avatar_url = current_user.avatar_url
    
    profile_data = UserProfile(
        nickname=current_user.username,  # 使用 username 作为昵称
        phone=current_user.phone,
        avatar=avatar_url,
        signature=signature
    )
    
    return BaseResponse(
        code=200,
        msg="获取成功",
        data=profile_data.model_dump()
    )


@router.put("/profile", response_model=BaseResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    更新用户个人资料（昵称、个性签名）
    """
    # 更新昵称（username）
    if profile_update.nickname:
        # 检查新昵称是否已被其他用户使用
        existing_user = await User.get_or_none(
            username=profile_update.nickname,
            is_deleted=False
        )
        if existing_user and existing_user.id != current_user.id:
            return BaseResponse(code=400, msg="该昵称已被使用")
        
        current_user.username = profile_update.nickname
    
    # 更新个性签名（存储在 notification_preferences 中）
    if profile_update.signature is not None:
        if current_user.notification_preferences is None:
            current_user.notification_preferences = {}
        elif not isinstance(current_user.notification_preferences, dict):
            current_user.notification_preferences = {}
        
        if profile_update.signature:
            current_user.notification_preferences["signature"] = profile_update.signature
        else:
            # 如果传入空字符串，删除 signature
            current_user.notification_preferences.pop("signature", None)
    
    await current_user.save()
    
    return BaseResponse(
        code=200,
        msg="资料更新成功",
        data={
            "nickname": current_user.username,
            "signature": current_user.notification_preferences.get("signature") if current_user.notification_preferences else None
        }
    )


@router.post("/avatar", response_model=BaseResponse)
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):

    """
    上传用户头像
    """

    # 检查文件类型
    if not avatar.content_type or not avatar.content_type.startswith('image/'):
        return BaseResponse(code=400, msg="请上传图片文件")
    
    # 检查文件大小（限制为 5MB）
    file_content = await avatar.read()
    if len(file_content) > 5 * 1024 * 1024:
        return BaseResponse(code=400, msg="图片大小不能超过 5MB")
    
    # 生成唯一文件名
    file_extension = os.path.splitext(avatar.filename)[1] or ".jpg"
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join("uploads", "avatars", filename)
    
    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 更新用户头像 URL（存储相对路径）
        relative_path = f"avatars/{filename}"
        current_user.avatar_url = relative_path
        await current_user.save()
        
        # 返回完整的访问 URL
        avatar_url = f"/uploads/{relative_path}"
        
        return BaseResponse(
            code=200,
            msg="头像上传成功",
            data={"avatarUrl": avatar_url}
        )
    except Exception as e:
        return BaseResponse(code=500, msg=f"头像上传失败: {str(e)}")


@router.put("/password", response_model=BaseResponse)
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """
    修改密码
    """
    # 验证原密码
    if not verify_password(password_change.oldPassword, current_user.password):
        return BaseResponse(code=400, msg="原密码错误")
    
    # 验证新密码不能与原密码相同
    if verify_password(password_change.newPassword, current_user.password):
        return BaseResponse(code=400, msg="新密码不能与原密码相同")
    
    # 验证新密码格式（至少8位）
    if len(password_change.newPassword) < 8:
        return BaseResponse(code=400, msg="新密码长度不能少于8位")

    
    # 更新密码
    current_user.password = get_password_hash(password_change.newPassword)
    await current_user.save()
    
    return BaseResponse(
        code=200,
        msg="密码修改成功"
    )


@router.post("/logout", response_model=BaseResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    退出登录
    """
    # 这里的逻辑主要依赖于前端：前端收到成功响应后，应删除 localStorage/Cookies 中的 Token。
    # 如果系统实现了 Redis Token 黑名单，应在此处将 Token 拉黑。

    return BaseResponse(
        code=200,
        msg="退出登录成功"
    )

@router.delete("/delete", response_model=BaseResponse)
async def delete_account(current_user: User = Depends(get_current_user)):
    """
    删除账户（软删除）
    """
    # 软删除：设置 is_deleted 标志
    current_user.is_deleted = True
    await current_user.save()
    
    # 可选：同时删除用户的所有植物（硬删除或软删除）
    # 由于 Plant 模型设置了 on_delete=CASCADE，如果硬删除用户，植物会自动删除
    # 这里我们只做软删除，所以植物不会被自动删除
    # 如果需要，可以手动软删除用户的植物：
    # await Plant.filter(user=current_user).update(is_deleted=True)
    
    return BaseResponse(
        code=200,
        msg="账户删除成功"
    )

@router.get("/stats", response_model=BaseResponse)
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """
    获取个人中心统计数据
    - plantCount: 用户植物总数
    - diaryCount: 日记数量
    - careDays: 养护天数（按账号注册天数计算）
    """
    # 统计植物数量
    plant_count = await Plant.filter(user=current_user, is_deleted=False).count()

    # 日记数量
    diary_count = await Diary.filter(user_id=current_user.id, is_deleted=False).count()

    # 养护天数：账号注册到今天的天数，至少为1
    if current_user.created_at:
        care_days = max((date.today() - current_user.created_at.date()).days + 1, 1)
    else:
        care_days = 1

    stats = UserStats(
        plantCount=plant_count,
        diaryCount=diary_count,
        careDays=care_days
    )

    return BaseResponse(
        code=200,
        msg="获取成功",
        data=stats.model_dump()
    )
