from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.infrastructure.database import db_helper
from src.infrastructure.repositories import SQLAlchemyUserRepository
from src.application.services import UserService


class UserServiceGetter(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with db_helper.session_getter() as session:
            user_repo = SQLAlchemyUserRepository(session)
            user_service = UserService(user_repo)
            data["user_service"] = user_service
            return await handler(event, data)
