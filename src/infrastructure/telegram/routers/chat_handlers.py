import asyncio

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.infrastructure.telegram.middlewares import (
    SaveUserDB,
    LobbyServiceGetter,
    AntiFlood,
)
from src.infrastructure.repositories.sqlalchemy_user_repo import (
    SQLAlchemyUserRepository,
)
from src.application.services import LobbyService
from src.application.schemas import UserSchema

router = Router()
router.message.middleware(SaveUserDB())
router.message.middleware(LobbyServiceGetter())
router.message.middleware(AntiFlood())

# @router.message(Command("check"))
# async def check_handler(
#     message: Message,
#     user_repo: SQLAlchemyUserRepository,
# ):
#     user = await user_repo.get_user_by_tg_id(tg_id=message.from_user.id)

#     if user:
#         text = (
#             f"Пользователь найден в бд.\n"
#             f"id: {user.id}\n"
#             f"username: {user.username}\n"
#             f"balance: {user.balance}\n"
#         )
#         await message.answer(text=text)
#         return

#     user_create = UserCreate(
#         tg_id=message.from_user.id,
#         username=message.from_user.username,
#     )
#     user = await user_repo.create_user(user_in=user_create)

#     text = (
#         f"Пользователь создан в бд.\n"
#         f"id: {user.id}\n"
#         f"username: {user.username}\n"
#         f"balance: {user.balance}\n"
#     )
#     await message.answer(text=text)


@router.message(Command("startgame"))
async def handle_start_game(
    message: Message,
    lobby_service: LobbyService,
):
    chat_id = message.chat.id
    lobby = await lobby_service.create_lobby(
        chat_id=chat_id,
        user_id=message.from_user.id,
    )
    if not lobby:
        await message.answer(f"Игра начата и так.")
        return

    text = (
        f"Возможно игра началась я ебу что ли\n"
        f"Игроки: {lobby.str_users()}\n"
        f"Таймер: 80"
    )
    msg = await message.answer(text=text)
    task = asyncio.create_task(
        lobby_service.lobby_timer(message=msg),
    )
    LobbyService.save_timer(
        chat_id=chat_id,
        message=msg,
        task=task,
    )


@router.message(Command("join"))
async def handle_join(
    message: Message,
    lobby_service: LobbyService,
):
    lobby = await lobby_service.add_user(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
    )
    if not lobby:
        await message.answer("Ты уже в игре.")
        return

    await message.answer(
        f"Пользователь {message.from_user.username} присоединился к игре."
    )


@router.message(Command("cancel"))
async def handle_cancel(
    message: Message,
    lobby_service: LobbyService,
):
    res = await lobby_service.cancel_lobby(message.chat.id)

    if not res:
        await message.answer("Начни игру для начала долбоеб.")
        return
    await message.answer("Набор на игру отменен.")
