from aiogram import Router
from aiogram.types import CallbackQuery

from infrastructure.telegram.middlewares import (
    SaveUserDB,
    GameServiceGetter,
    AntiFlood,
)
from infrastructure.telegram.routers.states import ChatState
from application.services import GameServiceTG
from utils.tg.filters import PlayerFilter, StandData, HitData
from utils.tg.functions import (
    pass_turn_next_player,
    format_player_info,
    new_turn_current_player,
)
from domain.types.game import SuccessType, ErrorType

router = Router()
router.callback_query.middleware(AntiFlood())
router.callback_query.middleware(SaveUserDB())
router.callback_query.middleware(GameServiceGetter())


async def process_not_success(
    callback: CallbackQuery,
    err_type: ErrorType,
):
    if err_type == ErrorType.PLAYER_NOT_FOUND:
        await callback.answer(text=f"Ты не в игре")
    elif err_type == ErrorType.ANOTHER_PLAYER_TURN:
        await callback.answer(text="Сейчас ходит другой игрок.")


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
    chat_id = callback.message.chat.id
    response = await game_service.player_turn_hit(
        chat_id=chat_id,
        user_tg_id=callback.from_user.id,
    )

    if not response.success:
        if not response.success:
            await process_not_success(callback, response.type)
            return

    await callback.answer()
    player = response.data.get("player")
    next_player = response.data.get("next_player")

    if response.type == SuccessType.HIT_ACCEPTED:
        await new_turn_current_player(callback.message, player, game_service)
        return
    elif response.type == SuccessType.HIT_BLACKJACK:
        await callback.message.edit_text(
            text=format_player_info(player, "блек-джек."),
        )
    elif response.type == SuccessType.HIT_BUSTED:
        await callback.message.edit_text(
            text=format_player_info(player, "перебор."),
        )

    if next_player is None:
        return

    await pass_turn_next_player(callback.message, next_player, game_service)


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
        await process_not_success(callback, response.type)
        return

    await callback.answer()
    player = response.data.get("player")
    await callback.message.answer(f"Игрок {player.get("player_name")} воздержался😂😂")

    next_player = response.data.get("next_player")
    if next_player is None:
        return

    await pass_turn_next_player(callback.message, next_player, game_service)
