from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Filter
from aiogram.filters.callback_data import CallbackData


class HitData(CallbackData, prefix="hit"):
    cur_player_id: int


class StandData(CallbackData, prefix="stand"):
    cur_player_id: int


def game_btns(player_id: int):
    hit_data = HitData(cur_player_id=player_id)
    stand_data = StandData(cur_player_id=player_id)
    hit = InlineKeyboardButton(text="Взять карту", callback_data=hit_data.pack())
    stand = InlineKeyboardButton(text="Абоба", callback_data=stand_data.pack())
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
