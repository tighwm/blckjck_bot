import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.infrastructure.telegram.middlewares import (
    SaveUserDB,
    GameServiceGetter,
    AntiFlood,
)
from src.infrastructure.telegram.routers.states import ChatState
from src.application.services import GameServiceTG
from src.infrastructure.telegram.routers.utils import (
    PlayerFilter,
    HitData,
    StandData,
    game_btns,
)
from src.domain.types.game import SuccessType, ErrorType

router = Router()
router.callback_query.middleware(AntiFlood())
router.callback_query.middleware(SaveUserDB())
router.callback_query.middleware(GameServiceGetter())


def format_player_info(
    player_data: dict,
    additionally: str | None = None,
) -> str:
    return (
        f"У игрока {player_data.get('player_name')} {additionally if additionally else ""}\n"
        f"Карты: {player_data.get('cards')}\n"
        f"Очки: {player_data.get('score')}"
    )


@router.callback_query(
    ChatState.game,
    HitData.filter(),
    PlayerFilter(1),
    flags={"rate_limit": 0.5},
)
async def hit_handler(
    callback: CallbackQuery,
    game_service: GameServiceTG,
):
    response = await game_service.player_turn_hit(
        chat_id=callback.message.chat.id,
        user_tg_id=callback.from_user.id,
    )

    if not response.success:
        if response.type == ErrorType.PLAYER_NOT_FOUND:
            await callback.answer(text=f"Ты не в игре бротон.")
        elif response.type == ErrorType.ANOTHER_PLAYER_TURN:
            await callback.answer(text="Сейчас ходит другой игрок.")
        return

    player = response.data.get("player")
    next_player = response.data.get("next_player")

    if response.type == SuccessType.HIT_ACCEPTED:
        await callback.message.edit_text(
            text=format_player_info(player),
            reply_markup=game_btns(player_id=player.get("player_id")),
        )
        return
    elif response.type == SuccessType.HIT_BLACKJACK:
        await callback.message.edit_text(text=format_player_info(player, "блекджек."))
    elif response.type == SuccessType.HIT_BUSTED:
        await callback.message.edit_text(text=format_player_info(player, "перебор."))

    if next_player is None:
        await callback.message.answer("Дилер учится делать ход.")
        return

    next_player_text = f"Ход игрока {next_player.get("player_name")}"
    next_player_id = next_player.get("player_id")
    msg = await callback.message.answer(
        text=next_player_text,
        reply_markup=game_btns(player_id=next_player_id),
    )

    game_service.set_turn_timer(message=msg, player_id=next_player_id)


@router.callback_query(
    ChatState.game,
    StandData.filter(),
    PlayerFilter(1),
    flags={"rate_limit": 0.5},
)
async def stand_handler(
    callback: CallbackQuery,
    game_service: GameServiceTG,
):
    response = await game_service.player_turn_stand(
        chat_id=callback.message.chat.id,
        user_tg_id=callback.from_user.id,
    )

    if not response.success:
        if response.type == ErrorType.PLAYER_NOT_FOUND:
            await callback.answer(text=f"Ты не в игре бротон.")
        elif response.type == ErrorType.ANOTHER_PLAYER_TURN:
            await callback.answer(text="Сейчас ходит другой игрок.")
        return

    player = response.data.get("player")
    await callback.message.answer(f"Игрок {player.get("player_name")} воздержался😂😂")

    next_player = response.data.get("next_player")

    if next_player is None:
        await callback.message.answer("Дилер учится делать ход.")
        return

    next_player_text = f"Ход игрока {next_player.get("player_name")}"
    next_player_id = next_player.get("player_id")
    msg = await callback.message.answer(
        text=next_player_text,
        reply_markup=game_btns(player_id=next_player_id),
    )

    game_service.set_turn_timer(message=msg, player_id=next_player_id)
