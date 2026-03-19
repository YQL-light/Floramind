from tortoise import fields, models
from app.models.user import User  # 导入你的 User 模型


class Plant(models.Model):
    # plant_id bigint 20 主键 自增
    id = fields.BigIntField(pk=True, source_field="plant_id")

    # 外键关联 User, on_delete=CASCADE 表示用户删除时植物也删除
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="plants", on_delete=fields.CASCADE
    )

    # 基础信息
    nickname = fields.CharField(max_length=50, description="植物昵称")
    species = fields.CharField(max_length=50, description="品种")
    icon = fields.CharField(max_length=20, default="🌱", description="植物图标/Emoji")
    plantAvatar_url = fields.CharField(max_length=255, null=True,default='plantAvatars/default_avatar.png')

    # 浇水相关
    last_watered = fields.DateField(null=True, description="上次浇水日期")
    water_cycle = fields.IntField(default=7, description="浇水周期(天)")

    # 施肥相关
    last_fertilized = fields.DateField(null=True, description="上次施肥日期")
    fertilize_cycle = fields.IntField(default=30, description="施肥周期(天)")

    # 环境要求 (可选)
    light_requirements = fields.CharField(max_length=20, default="medium", null=True)
    temperature_range = fields.CharField(max_length=20, default="18-25", null=True)

    # 系统字段
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_deleted = fields.BooleanField(default=False)

    class Meta:
        table = "plants"

    def __str__(self):
        return f"{self.nickname} ({self.species})"