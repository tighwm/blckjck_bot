from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter, CommandObject
from aiogram.types import Message

from application.services import LobbyServiceTG
from application.services.timer_mng import timer_manager
from infrastructure.telegram.routers.states import ChatState
from infrastructure.telegram.middlewares import (
    SaveUserDB,
    LobbyServiceGetter,
    AntiFlood,
)
from utils.tg.filters import ChatTypeFilter
from utils.tg.functions import get_user_mention

router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(SaveUserDB())
router.message.middleware(LobbyServiceGetter())


async def start_update_lobby_text_timer(
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


@router.message(
    ChatTypeFilter(["group", "supergroup"]),
    Command("leave"),
    ChatState.lobby,
)
async def handle_leave(message: Message, lobby_service: LobbyServiceTG):
    await lobby_service.remove_user(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
    )
    user_mention = get_user_mention(message.from_user.first_name, message.from_user.id)
    text = f"{user_mention} покинул лобби\\."
    await message.answer(
        text=text,
        parse_mode="MarkdownV2",
    )


@router.message(
    ChatTypeFilter(["group", "supergroup"]),
    Command("cancel"),
    ChatState.lobby,
)
async def handle_cancel(
    message: Message,
    lobby_service: LobbyServiceTG,
    state: FSMContext,
):
    await lobby_service.cancel_lobby(message.chat.id)

    timer_manager.cancel_timer(timer_type="lobby:interval", chat_id=message.chat.id)
    await state.clear()
    await message.answer("Набор на игру отменен.")


@router.message(
    ChatTypeFilter(["group", "supergroup"]),
    Command("join"),
    ChatState.lobby,
)
async def handle_join(
    message: Message,
    lobby_service: LobbyServiceTG,
):
    user_id = message.from_user.id
    name = message.from_user.first_name
    lobby = await lobby_service.add_user(
        chat_id=message.chat.id,
        user_id=user_id,
        first_name=name,
    )
    if lobby is None:
        await message.answer("Ты уже в игре.")
        return

    await message.answer(
        f"Пользователь {get_user_mention(name, user_id)} присоединился к игре\\.",
        parse_mode="MarkdownV2",
    )


def get_timeout_arg(text: str):
    if text is not None:
        text = text.split()
    else:
        return 50
    if text[0].isdigit():
        timeout = int(text[0])
        if 15 <= timeout <= 600:
            return timeout
        return None
    else:
        return None


@router.message(
    ChatTypeFilter(["group", "supergroup"]),
    Command("lobby"),
    StateFilter(None),
    flags={"rate_limit": 1.0},
)
async def handle_lobby(
    message: Message,
    lobby_service: LobbyServiceTG,
    state: FSMContext,
    command: CommandObject,
):
    command_args = command.args
    timeout = get_timeout_arg(command_args)
    if timeout is None:
        await message.answer(
            "Аргумент времени таймера должен быть числом, не менее 15 и не более 600 (секунд)."
        )
        return

    chat_id = message.chat.id
    lobby = await lobby_service.create_lobby(
        chat_id=chat_id,
        user_id=message.from_user.id,
        timeout=timeout,
        first_name=message.from_user.first_name,
    )
    if not lobby:
        await message.answer(f"Игра начата и так.")
        return

    await state.set_state(ChatState.lobby)
    await start_update_lobby_text_timer(
        message,
        timeout,
        lobby.names,
        lobby_service,
    )
