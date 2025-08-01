from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from infrastructure.repositories import (
    RedisLobbyCacheRepoTG,
)
from infrastructure.redis_py.redis_helper import redis_helper
from application.services import LobbyServiceTG


class LobbyServiceGetter(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_repo = data.get("user_repo")
        cache_repo = RedisLobbyCacheRepoTG(redis=redis_helper.get_redis_client())
        lobby_service = LobbyServiceTG(
            lobby_repo=cache_repo,
            user_repo=user_repo,
        )
        data["lobby_service"] = lobby_service
        return await handler(event, data)
