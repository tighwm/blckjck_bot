from redis.asyncio import Redis, ConnectionPool

from infrastructure.config import settings


class RedisHelper:
    def __init__(
        self,
        max_connections: int = 15,
    ):
        self.pool = ConnectionPool(
            max_connections=max_connections,
        ).from_url(str(settings.redis.url))

    def get_redis_client(self):
        client = Redis.from_pool(self.pool)
        return client


redis_helper = RedisHelper()
