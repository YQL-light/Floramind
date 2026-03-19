from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "users" (
    "user_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "phone" VARCHAR(20),
    "password" VARCHAR(255) NOT NULL,
    "avatar_url" VARCHAR(255),
    "location_city" VARCHAR(100),
    "notification_preferences" JSONB,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "security_answer" VARCHAR(255)
);
COMMENT ON COLUMN "users"."security_answer" IS '密保问题答案：您最喜欢的植物是什么？';
CREATE TABLE IF NOT EXISTS "plants" (
    "plant_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "nickname" VARCHAR(50) NOT NULL,
    "species" VARCHAR(50) NOT NULL,
    "last_watered" DATE,
    "water_cycle" INT NOT NULL DEFAULT 7,
    "last_fertilized" DATE,
    "fertilize_cycle" INT NOT NULL DEFAULT 30,
    "light_requirements" VARCHAR(20) DEFAULT 'medium',
    "temperature_range" VARCHAR(20) DEFAULT '18-25',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("user_id") ON DELETE CASCADE
);
COMMENT ON COLUMN "plants"."nickname" IS '植物昵称';
COMMENT ON COLUMN "plants"."species" IS '品种';
COMMENT ON COLUMN "plants"."last_watered" IS '上次浇水日期';
COMMENT ON COLUMN "plants"."water_cycle" IS '浇水周期(天)';
COMMENT ON COLUMN "plants"."last_fertilized" IS '上次施肥日期';
COMMENT ON COLUMN "plants"."fertilize_cycle" IS '施肥周期(天)';
CREATE TABLE IF NOT EXISTS "diaries" (
    "diary_id" BIGSERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(100),
    "content" TEXT NOT NULL,
    "activity_type" VARCHAR(50),
    "weather" VARCHAR(50) DEFAULT 'sunny',
    "temperature" VARCHAR(50),
    "images" JSONB,
    "diary_date" DATE NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_deleted" BOOL NOT NULL DEFAULT False,
    "plant_id" BIGINT NOT NULL REFERENCES "plants" ("plant_id") ON DELETE CASCADE,
    "user_id" BIGINT NOT NULL REFERENCES "users" ("user_id") ON DELETE CASCADE
);
COMMENT ON COLUMN "diaries"."title" IS '日记标题';
COMMENT ON COLUMN "diaries"."content" IS '日记内容';
COMMENT ON COLUMN "diaries"."activity_type" IS '活动类型：watering, fertilizing, etc.';
COMMENT ON COLUMN "diaries"."temperature" IS '温度范围，如：6°C-15°C';
COMMENT ON COLUMN "diaries"."images" IS '图片URL列表';
COMMENT ON COLUMN "diaries"."diary_date" IS '日记记录的日期';
COMMENT ON TABLE "diaries" IS '植物日记数据模型';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
