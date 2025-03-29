from redis.asyncio import Redis

from src.infrastructure.config import settings


class RedisSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = Redis.from_url(str(settings.redis.url))
        return cls._instance
