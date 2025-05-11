from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import Message

from application.services import LobbyServiceTG
from application.services.timer_mng import timer_manager
from infrastructure.telegram.routers.states import ChatState
from infrastructure.telegram.middlewares import (
    SaveUserDB,
    LobbyServiceGetter,
    AntiFlood,
)


router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(SaveUserDB())
router.message.middleware(LobbyServiceGetter())


async def start_lobby_timer(
    message: Message,
    timeout: int,
    players: str,
    lobby_service: LobbyServiceTG,
):
    text = f"Запущено лобби на игру.\n" f"Игроки: {players}\n" f"Таймер: {timeout}"
    msg = await message.answer(text=text)
    timer_manager.create_interval_timer(
        "lobby:interval",
        message.chat.id,
        lobby_service.lobby_interval_timer,
        None,
        timeout,
        5,
        msg,
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
    timer_manager.cancel_timer(timer_type="lobby:interval", chat_id=message.chat.id)


@router.message(Command("join"), ChatState.lobby)
async def handle_join(
    message: Message,
    lobby_service: LobbyServiceTG,
):
    lobby = await lobby_service.add_user(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
    )
    if lobby is None:
        await message.answer("Ты уже в игре.")
        return

    await message.answer(
        f"Пользователь {message.from_user.username} присоединился к игре."
    )


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
    await start_lobby_timer(message, timeout, lobby.str_users(), lobby_service)
