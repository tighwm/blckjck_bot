from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message

from infrastructure.database import db_helper
from infrastructure.repositories.sqlalchemy_user_repo import (
    SQLAlchemyUserRepositoryTG,
)
from application.schemas import UserCreate


class SaveUserDB(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with db_helper.ctx_session_getter() as session:
            user_id = event.from_user.id
            user_repo = SQLAlchemyUserRepositoryTG(session)
            data["user_repo"] = user_repo
            user_schema = await user_repo.get_user_by_tg_id(tg_id=user_id)
            if user_schema:
                return await handler(event, data)
            new_user = UserCreate(
                tg_id=user_id,
                username=event.from_user.username,
            )
            await user_repo.create_user(user_in=new_user)
            return await handler(event, data)
