from datetime import datetime, timedelta, timezone
from typing import Union, Any
from jose import jwt
import bcrypt  # 直接导入 bcrypt
from app.core.config import settings


# -----------------------------------------------------------
# 密码加密与校验 (不再使用 passlib)
# -----------------------------------------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验密码
    :param plain_password: 用户输入的明文密码
    :param hashed_password: 数据库存的哈希密码
    """
    # bcrypt 需要字节(bytes)类型，且 hash 也是字节类型
    # 如果数据库取出的 hashed_password 是 str，需要 encode 为 bytes
    if isinstance(hashed_password, str):
        hashed_password_bytes = hashed_password.encode('utf-8')
    else:
        hashed_password_bytes = hashed_password

    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password_bytes
        )
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    """
    # 1. 转为 bytes
    pwd_bytes = password.encode('utf-8')
    # 2. 生成盐并加密
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    # 3.以此为了存入数据库方便，将 bytes 解码回 str
    return hashed.decode('utf-8')


# -----------------------------------------------------------
# JWT Token 生成
# -----------------------------------------------------------

def create_access_token(subject: Union[str, Any]) -> str:
    # 使用 UTC 时间
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"sub": str(subject), "exp": expire}

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt