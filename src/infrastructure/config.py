from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, PostgresDsn, RedisDsn
from dotenv import load_dotenv

load_dotenv()


class DBsettings(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


class BotSettings(BaseModel):
    token: str


class RedisSettings(BaseModel):
    url: RedisDsn


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        case_sensitive=False,
    )

    db: DBsettings
    bot: BotSettings
    redis: RedisSettings


settings = Settings()
