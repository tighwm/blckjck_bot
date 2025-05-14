from typing import TYPE_CHECKING

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from application.schemas import UserSchema
from application.services.timer_mng import timer_manager
from utils.tg.filters import StandData, HitData

if TYPE_CHECKING:
    from application.services import GameServiceTG


def game_btns(player_id: int):
    hit_data = HitData(cur_player_id=player_id)
    stand_data = StandData(cur_player_id=player_id)
    hit = InlineKeyboardButton(text="Взять карту", callback_data=hit_data.pack())
    stand = InlineKeyboardButton(text="Воздержаться💀", callback_data=stand_data.pack())
    row = [hit, stand]
    rows = [row]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup


def format_player_info(
    player_data: dict,
    additionally: str | None = None,
) -> str:
    return (
        f"У игрока {player_data.get('player_name')} {additionally if additionally else ""}\n"
        f"Карты: {player_data.get('cards')}\n"
        f"Очки: {player_data.get('score')}"
    )


def format_user_profile(user_schema: UserSchema) -> str:
    return f"Профиль юзера {user_schema.username}\n" f"Баланс: {user_schema.balance}"


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
