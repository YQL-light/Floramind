from tortoise import fields, models
from app.models.user import User
from app.models.plant import Plant


class Diary(models.Model):
    """
    植物日记数据模型
    """
    # diary_id
    id = fields.BigIntField(pk=True, source_field="diary_id")

    # 关联用户
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="diaries", on_delete=fields.CASCADE
    )

    # 关联植物
    plant: fields.ForeignKeyRelation[Plant] = fields.ForeignKeyField(
        "models.Plant", related_name="diaries", on_delete=fields.CASCADE
    )

    # 标题字段
    title = fields.CharField(max_length=100, null=True, description="日记标题")

    # 日记内容
    content = fields.TextField(description="日记内容")

    # 养护活动类型
    activity_type = fields.CharField(
        max_length=50,
        null=True,
        description="活动类型：watering, fertilizing, etc."
    )

    # 天气信息
    weather = fields.CharField(
        max_length=50,
        null=True,
        default="sunny"
    )

    # 温度范围
    temperature = fields.CharField(
        max_length=50,
        null=True,
        description="温度范围，如：6°C-15°C"
    )

    # 图片URL列表 (PostgreSQL JSONB)
    images = fields.JSONField(
        null=True,
        default=list,
        description="图片URL列表"
    )

    # 日记日期
    diary_date = fields.DateField(description="日记记录的日期")

    # 系统字段
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)

    class Meta:
        table = "diaries"
        ordering = ["-diary_date", "-created_at"]

    def __str__(self):
        # 这里的 self.title 现在安全了
        return f"日记ID:{self.id} - {self.title or '无标题'}"

    # 删除了 to_frontend_format，逻辑后移至 API 层处理