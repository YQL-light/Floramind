# app/models/user.py
from tortoise import fields, models


class User(models.Model):
    # user_id bigint 20 主键 自增
    id = fields.BigIntField(pk=True, source_field="user_id")

    # username varchar 50 非空
    username = fields.CharField(max_length=50, unique=True)

    # email varchar 100 非空 (虽然你希望简化注册，但数据库约束了非空，建议注册时必填，或后台生成假邮箱)
    email = fields.CharField(max_length=100, unique=True)

    # phone varchar 20 可空
    phone = fields.CharField(max_length=20, null=True)

    # password varchar 255 非空
    password = fields.CharField(max_length=255)

    # avatar_url varchar 255 可空
    avatar_url = fields.CharField(max_length=255, null=True)

    # location_city varchar 100 可空
    location_city = fields.CharField(max_length=100, null=True)

    # notification_preferences json 可空
    notification_preferences = fields.JSONField(null=True)

    # created_at datetime 非空 默认当前时间
    created_at = fields.DatetimeField(auto_now_add=True)

    # updated_at datetime 非空 默认当前时间
    updated_at = fields.DatetimeField(auto_now=True)

    # is_deleted tinyint 1 非空 默认0
    is_deleted = fields.BooleanField(default=False)

    # 存储密保问题的答案
    security_answer = fields.CharField(max_length=255, null=True, description="密保问题答案：您最喜欢的植物是什么？")

    class Meta:
        table = "users"  # 指定数据库表名