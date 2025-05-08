import asyncio

from aiogram import Router, F
from aiogram.types import CallbackQuery

from infrastructure.telegram.middlewares import (
    SaveUserDB,
    GameServiceGetter,
    AntiFlood,
)
from infrastructure.telegram.routers.states import ChatState
from application.services import GameServiceTG
from utils.tg_utils import (
    PlayerFilter,
    HitData,
    StandData,
    game_btns,
    format_player_info,
)
from domain.types.game import SuccessType, ErrorType

router = Router()
router.callback_query.middleware(AntiFlood())
router.callback_query.middleware(SaveUserDB())
router.callback_query.middleware(GameServiceGetter())


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
        if response.type == ErrorType.PLAYER_NOT_FOUND:
            await callback.answer(text=f"Ты не в игре.")
        elif response.type == ErrorType.ANOTHER_PLAYER_TURN:
            await callback.answer(text="Сейчас ходит другой игрок.")
        return

    player = response.data.get("player")
    next_player = response.data.get("next_player")

    if response.type == SuccessType.HIT_ACCEPTED:
        player_id = player.get("player_id")
        await callback.message.edit_text(
            text=format_player_info(player),
            reply_markup=game_btns(player_id=player_id),
        )
        timer_manager.create_timer(
            "game:turn",
            chat_id,
            game_service.kick_afk,
            player_id,
            30,
            callback.message,
        )

        return
    elif response.type == SuccessType.HIT_BLACKJACK:
        await callback.message.edit_text(text=format_player_info(player, "блекджек."))
    elif response.type == SuccessType.HIT_BUSTED:
        await callback.message.edit_text(text=format_player_info(player, "перебор."))

    if next_player is None:
        return

    next_player_text = f"Ход игрока {next_player.get("player_name")}"
    next_player_id = next_player.get("player_id")
    msg = await callback.message.answer(
        text=next_player_text,
        reply_markup=game_btns(player_id=next_player_id),
    )
    timer_manager.create_timer(
        "game:turn",
        chat_id,
        game_service.kick_afk,
        next_player_id,
        30,
        msg,
    )


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
            await callback.answer(text=f"Ты не в игре")
        elif response.type == ErrorType.ANOTHER_PLAYER_TURN:
            await callback.answer(text="Сейчас ходит другой игрок.")
        return

    player = response.data.get("player")
    await callback.message.answer(f"Игрок {player.get("player_name")} воздержался😂😂")

    next_player = response.data.get("next_player")
    if next_player is None:
        return

    next_player_text = f"Ход игрока {next_player.get("player_name")}"
    next_player_id = next_player.get("player_id")
    msg = await callback.message.answer(
        text=next_player_text,
        reply_markup=game_btns(player_id=next_player_id),
    )
    timer_manager.create_timer(
        "game:turn",
        msg.chat.id,
        game_service.kick_afk,
        next_player_id,
        30,
        msg,
    )
