from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.infrastructure.database import db_helper
from src.infrastructure.repositories.sqlalchemy_user_repo import (
    SQLAlchemyUserRepository,
)


class UserRepoMaker(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with db_helper.session_getter() as session:
            data["user_repo"] = SQLAlchemyUserRepository(session)
            return await handler(event, data)
