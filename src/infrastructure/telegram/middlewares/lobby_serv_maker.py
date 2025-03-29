from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.infrastructure.database import db_helper
from src.infrastructure.repositories import (
    SQLAlchemyUserRepository,
    RedisLobbyCacheRepo,
)
from src.infrastructure.redis_py.client import RedisSingleton
from src.application.services import LobbyService


class LobbyServiceGetter(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with db_helper.session_getter() as session:
            user_repo = SQLAlchemyUserRepository(session)
            cache_repo = RedisLobbyCacheRepo(redis=RedisSingleton())
            lobby_service = LobbyService(
                lobby_repo=cache_repo,
                user_repo=user_repo,
            )
            data["lobby_service"] = lobby_service
            return await handler(event, data)
