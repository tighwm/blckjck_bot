from redis.asyncio import Redis

from application.interfaces import LeaderBoardInterface


class RedisLeaderBoardRepo(LeaderBoardInterface):
    def __init__(
        self,
        redis: Redis,
    ):
        self.redis = redis

    async def get_leaderboard(
        self,
        board: str,
        zrange: tuple[int, int] = (0, 9),
    ):
        start, end = zrange
        return await self.redis.zrevrange(
            name=board,
            start=start,
            end=end,
            withscores=True,
        )

    async def cache_leaderboard(
        self,
        board: str,
        members: dict[str, int] = None,
    ):
        await self.redis.zadd(name=board, mapping=members)
