from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from infrastructure.repositories import RedisGameCacheRepo
from infrastructure.redis_py.redis_helper import redis_helper
from application.services import GameServiceTG


class GameServiceGetter(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_repo = data.get("user_repo")
        cache_repo = RedisGameCacheRepo(redis=redis_helper.get_redis_client())
        game_service = GameServiceTG(
            user_repo=user_repo,
            game_repo=cache_repo,
        )
        data["game_service"] = game_service
        return await handler(event, data)
