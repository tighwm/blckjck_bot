from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from infrastructure.redis_py.redis_helper import redis_helper
from infrastructure.repositories import RedisLeaderBoardRepo
from application.services import CommandService


class CommandServiceGetter(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        user_repo = data.get("user_repo")
        redis = redis_helper.get_redis_client()
        board_repo = RedisLeaderBoardRepo(redis)
        com_service = CommandService(
            user_repo=user_repo,
            board_repo=board_repo,
        )
        data["com_service"] = com_service
        return await handler(event, data)
