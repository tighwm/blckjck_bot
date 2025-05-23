import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from application.services import (
    GameServiceTG,
)
from application.services.types import ResponseType
from domain.entities import PlayerResult
from infrastructure.telegram.middlewares import (
    SaveUserDB,
    GameServiceGetter,
    AntiFlood,
)
from infrastructure.telegram.routers.states import ChatState
from utils.tg.filters import PlayerFilter, StandData, HitData
from utils.tg.functions import (
    format_player_info,
    new_turn_current_player,
    handle_post_player_action,
)

logger = logging.getLogger(__name__)

router = Router()

callback_middlewares = [
    AntiFlood(),
    SaveUserDB(),
    GameServiceGetter(),
]
for middleware in callback_middlewares:
    router.callback_query.middleware(middleware)


async def process_unsuccessful_response(
    callback: CallbackQuery,
    error_type: ResponseType,
):
    error_messages = {
        ResponseType.PLAYER_NOT_FOUND: "Ты не в игре.",
        ResponseType.ANOTHER_PLAYER_TURN: "Сейчас ходит другой игрок.",
    }
    message_text = error_messages.get(error_type, "Произошла неизвестная ошибка.")
    await callback.answer(text=message_text, show_alert=True)


@router.callback_query(
    ChatState.game,
    HitData.filter(),
    PlayerFilter(1),
    flags={"rate_limit": 0.5},
)
async def hit_action_handler(
    callback: CallbackQuery,
    game_service: GameServiceTG,
):
    if not callback.message:
        logger.error("CallbackQuery has no message attribute in hit_action_handler")
        await callback.answer("Произошла ошибка: сообщение не найдено.")
        return

    chat_id = callback.message.chat.id
    user_tg_id = callback.from_user.id

    response = await game_service.player_turn_hit(
        chat_id=chat_id,
        user_tg_id=user_tg_id,
    )

    if response is None:
        logger.error(
            "GameService returned None for hit action. Chat: %r, User: %r",
            chat_id,
            user_tg_id,
        )
        await callback.message.answer("Ошибка: Сервис игры не ответил.")
        return
    if not response.success:
        await process_unsuccessful_response(callback, response.type)
        return

    await callback.answer()

    player_data = response.data.get("player")
    if not player_data:
        logger.error(
            "No player data in successful hit response. Chat: %r, User: %r",
            chat_id,
            user_tg_id,
        )
        await callback.message.edit_text("Ошибка: не найдены данные игрока.")
        return

    player_result = player_data.get("result")
    action_taken = False

    if player_result == PlayerResult.BLACKJACK:
        await callback.message.edit_text(
            text=format_player_info(player_data, "блек-джек."),
        )
        action_taken = True
    elif player_result == PlayerResult.BUST:
        await callback.message.edit_text(
            text=format_player_info(player_data, "перебор."),
        )
        action_taken = True
    elif response.type == ResponseType.HIT_ACCEPTED:
        await new_turn_current_player(
            message=callback.message,
            player=player_data,
            game_service=game_service,
        )
        return
    else:
        logger.warning(
            "Unexpected player result or response type after hit. Player: %r, Response: %r",
            player_data,
            response,
        )

    if action_taken:
        await handle_post_player_action(response.data, callback.message, game_service)
    # Если action_taken = False и это не HIT_ACCEPTED, возможно, стоит что-то сделать или залогировать


@router.callback_query(
    ChatState.game,
    StandData.filter(),
    PlayerFilter(1),
    flags={"rate_limit": 0.5},
)
async def stand_action_handler(
    callback: CallbackQuery,
    game_service: GameServiceTG,
):

    if not callback.message:
        logger.error("CallbackQuery has no message attribute in stand_action_handler")
        await callback.answer("Произошла ошибка: сообщение не найдено.")
        return

    chat_id = callback.message.chat.id
    user_tg_id = callback.from_user.id

    response = await game_service.player_turn_stand(
        chat_id=chat_id,
        user_tg_id=user_tg_id,
    )

    if response is None:
        logger.error(
            "GameService returned None for stand action. Chat: %r, User: %r",
            chat_id,
            user_tg_id,
        )
        await callback.message.answer("Ошибка: Сервис игры не ответил.")
        return
    if not response.success:
        await process_unsuccessful_response(callback, response.type)
        return

    await callback.answer()

    player_data = response.data.get("player")
    if not player_data:
        logger.error(
            "No player data in successful stand response. Chat: %r, User: %r",
            chat_id,
            user_tg_id,
        )
        return

    await callback.message.answer(
        f"Игрок {player_data.get('player_name', 'Неизвестный игрок')} воздержался."
    )
    await callback.message.edit_reply_markup(reply_markup=None)

    await handle_post_player_action(response.data, callback.message, game_service)
