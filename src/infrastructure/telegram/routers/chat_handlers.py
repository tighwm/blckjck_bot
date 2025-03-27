from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.infrastructure.telegram.middlewares.user_repo_maker import UserRepoMaker
from src.infrastructure.repositories.sqlalchemy_user_repo import (
    SQLAlchemyUserRepository,
)
from src.application.schemas.user import UserCreate

router = Router()
router.message.middleware(UserRepoMaker())


@router.message(Command("check"))
async def check_handler(
    message: Message,
    user_repo: SQLAlchemyUserRepository,
):
    user = await user_repo.get_user_by_tg_id(tg_id=message.from_user.id)

    if user:
        text = (
            f"Пользователь найден в бд.\n"
            f"id: {user.id}\n"
            f"username: {user.username}\n"
            f"balance: {user.balance}\n"
        )
        await message.answer(text=text)
        return

    user_create = UserCreate(
        tg_id=message.from_user.id,
        username=message.from_user.username,
    )
    user = await user_repo.create_user(user_in=user_create)

    text = (
        f"Пользователь создан в бд.\n"
        f"id: {user.id}\n"
        f"username: {user.username}\n"
        f"balance: {user.balance}\n"
    )
    await message.answer(text=text)
