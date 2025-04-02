from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.infrastructure.database import db_helper
from src.infrastructure.repositories import (
    SQLAlchemyUserRepository,
    RedisGameCacheRepo,
)
from src.infrastructure.redis_py.client import RedisSingleton
from src.application.services import GameServiceTG


class GameServiceGetter(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with db_helper.session_getter() as session:
            user_repo = SQLAlchemyUserRepository(session)
            cache_repo = RedisGameCacheRepo(redis=RedisSingleton())
            game_service = GameServiceTG(
                user_repo=user_repo,
                game_repo=cache_repo,
            )
            data["game_service"] = game_service
            return await handler(event, data)
