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
from src.domain.types.game import SuccessType

router = Router()
router.callback_query.middleware(AntiFlood())
router.callback_query.middleware(SaveUserDB())
router.callback_query.middleware(GameServiceGetter())


def format_player_info(player_data: dict) -> str:
    return (
        f"Ход игрока {player_data.get('player_name')}\n"
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

    player = response.data.get("player")
    next_player = response.data.get("next_player")

    if response.type == SuccessType.HIT_ACCEPTED:
        await callback.message.edit_text(
            text=format_player_info(player),
            reply_markup=game_btns(player_id=player.get("player_id")),
        )
        return
    elif response.type in (SuccessType.HIT_BLACKJACK, SuccessType.HIT_BUSTED):
        await callback.message.edit_text(text=format_player_info(player))

    if next_player is None:
        await callback.message.answer("Дилер учится делать ход.")
        return

    next_player_text = f"Ход игрока {next_player.get("player_name")}"
    await callback.message.answer(
        text=next_player_text,
        reply_markup=game_btns(player_id=next_player.get("player_id")),
    )


@router.callback_query(
    ChatState.game,
    StandData.filter(),
    PlayerFilter(1),
    flags={"rate_limit": 0.5},
)
async def hit_handler(
    callback: CallbackQuery,
    game_service: GameServiceTG,
):
    await callback.answer("222222")
