import asyncio

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.infrastructure.telegram.middlewares import (
    SaveUserDB,
    LobbyServiceGetter,
    AntiFlood,
    GameServiceGetter,
)
from src.application.services import LobbyServiceTG, GameServiceTG
from src.infrastructure.telegram.routers.states import ChatState
from src.domain.types.game import SuccessType, ErrorType
from src.infrastructure.telegram.routers.utils import game_btns

router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(SaveUserDB())
router.message.middleware(LobbyServiceGetter())
router.message.middleware(GameServiceGetter())

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


@router.message(Command("startgame"), StateFilter(None), flags={"rate_limit": 1.0})
async def handle_start_game(
    message: Message,
    lobby_service: LobbyServiceTG,
    state: FSMContext,
):
    chat_id = message.chat.id
    lobby = await lobby_service.create_lobby(
        chat_id=chat_id,
        user_id=message.from_user.id,
    )
    if not lobby:
        await message.answer(f"Игра начата и так.")
        return

    await state.set_state(ChatState.lobby)
    text = (
        f"Возможно игра началась я ебу что ли\n"
        f"Игроки: {lobby.str_users()}\n"
        f"Таймер: 80"
    )
    msg = await message.answer(text=text)
    task = asyncio.create_task(
        lobby_service.lobby_timer(
            message=msg,
            state=state,
        ),
    )
    LobbyServiceTG.save_timer(
        chat_id=chat_id,
        message=msg,
        task=task,
    )


@router.message(Command("join"), ChatState.lobby)
async def handle_join(
    message: Message,
    lobby_service: LobbyServiceTG,
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


@router.message(Command("cancel"), ChatState.lobby)
async def handle_cancel(
    message: Message,
    lobby_service: LobbyServiceTG,
):
    res = await lobby_service.cancel_lobby(message.chat.id)

    if not res:
        await message.answer("Начни игру для начала долбоеб.")
        return
    await message.answer("Набор на игру отменен.")


# Регулярное выражение для фильтрации ставок от 1 и без чувствительности к регистру
filters_on_bid = F.text.regexp(r"(?i)^ставка\s([1-9]\d*)$")


@router.message(filters_on_bid, ChatState.bid)
async def bid_handle(
    message: Message,
    state: FSMContext,
    game_service: GameServiceTG,
):
    user_bid = int(message.text.split()[1])  # Получаем ставку из "ставка (число)"
    if user_bid < 5:
        await message.answer("Ставка не дожна быть менее 5")
        return

    response = await game_service.player_set_bid(
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        bid=user_bid,
    )
    if response is None:
        await message.answer("Копейки пересчитай свои.")
        return

    if response.type == SuccessType.BID_ACCEPTED:
        await message.answer("Ставка принята.")
    if response.type == SuccessType.ALL_PLAYERS_BET:
        await state.set_state(ChatState.game)
        player = response.data.get("player")
        await message.answer(
            text=f"Ход игрока {player.get("player_name")}",
            reply_markup=game_btns(player.get("player_id")),
        )
