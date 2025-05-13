from typing import Any, TYPE_CHECKING

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
    Message,
)
from aiogram.filters import Filter
from aiogram.filters.callback_data import CallbackData

from application.services.timer_mng import timer_manager

if TYPE_CHECKING:
    from application.services import GameServiceTG


class HitData(CallbackData, prefix="hit"):
    cur_player_id: int


class StandData(CallbackData, prefix="stand"):
    cur_player_id: int


def game_btns(player_id: int):
    hit_data = HitData(cur_player_id=player_id)
    stand_data = StandData(cur_player_id=player_id)
    hit = InlineKeyboardButton(text="Взять карту", callback_data=hit_data.pack())
    stand = InlineKeyboardButton(text="Воздержаться💀", callback_data=stand_data.pack())
    row = [hit, stand]
    rows = [row]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup


class PlayerFilter(Filter):
    def __init__(self, lol):
        self.kek = lol

    async def __call__(
        self,
        callback: CallbackQuery,
    ) -> bool:
        cur_player_id = int(callback.data.split(":")[1])
        if cur_player_id != callback.from_user.id:
            await callback.answer("Не твой ход.")
            return False
        return True


def format_player_info(
    player_data: dict,
    additionally: str | None = None,
) -> str:
    return (
        f"У игрока {player_data.get('player_name')} {additionally if additionally else ""}\n"
        f"Карты: {player_data.get('cards')}\n"
        f"Очки: {player_data.get('score')}"
    )


def format_user_profile(user_data: dict[str, Any]) -> str:
    return (
        f"Профиль юзера {user_data.get("username")}\n"
        f"Баланс: {user_data.get("balance")}"
    )


async def pass_turn_next_player(
    message: Message,
    player: dict,
    game_service: "GameServiceTG",
):
    player_id = player.get("player_id")
    text = f"Ход игрока {player.get("player_name")}"
    msg = await message.answer(
        text=text,
        reply_markup=game_btns(player_id),
    )
    timer_manager.create_timer(
        "game:turn",
        msg.chat.id,
        game_service.kick_afk,
        player_id,
        30,
        msg,
        player_id,
    )


async def new_turn_current_player(
    message: Message,
    player: dict,
    game_service: "GameServiceTG",
):
    player_id = player.get("player_id")
    text = format_player_info(player)
    await message.edit_text(
        text=text,
        reply_markup=game_btns(player_id=player_id),
    )
    timer_manager.create_timer(
        "game:turn",
        message.chat.id,
        game_service.kick_afk,
        player_id,
        30,
        message,
        player_id,
    )
