import asyncio
import logging
from typing import Any

from aiogram import Router
from aiogram.types import CallbackQuery, Message

from application.services.game_serviceTG import (
    ResponseType,
    GameServiceTG,
)
from domain.entities import PlayerResult
from infrastructure.telegram.middlewares import (
    SaveUserDB,
    GameServiceGetter,
    AntiFlood,
)
from infrastructure.telegram.routers.states import ChatState
from utils.tg.filters import PlayerFilter, StandData, HitData
from utils.tg.functions import (
    pass_turn_next_player,
    format_player_info,
    new_turn_current_player,
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


def format_dealer_reveal_text(data: dict[str, Any]) -> str:
    dealer = data.get("dealer", {})
    score_with_secret = dealer.get("score_with_secret")
    text_intro = (
        "У дилера блек-джек!"
        if score_with_secret == 21
        else "Дилер раскрывает вторую карту..."
    )

    return (
        f"{text_intro}\n"
        f"Первая: {dealer.get('first_card')}\n"
        f"Вторая: {dealer.get('secret_card')}\n"
        f"Очки: {score_with_secret}\n"
    )


def format_ending_result_text(data: dict[str, Any]) -> str:
    win_players = data.get("wins", [])
    push_players = data.get("push", [])
    lose_players = data.get("lose", [])

    parts = []
    if win_players:
        win_player_names = [player.get("player_name") for player in win_players]
        parts.append(f"Выиграли у крупье: {', '.join(win_player_names)}")
    if push_players:
        push_player_names = [player.get("player_name") for player in push_players]
        parts.append(f"В ничью сыграли: {', '.join(push_player_names)}")
    if lose_players:
        lose_player_names = [player.get("player_name") for player in lose_players]
        parts.append(f"Проиграли ставку: {', '.join(lose_player_names)}")

    return "\n".join(parts) if parts else "Нет результатов для отображения."


async def handle_dealer_turns(
    dealer_action_data: dict[str, Any],
    message: Message,
    game_service: GameServiceTG,
):
    dealer_turns = dealer_action_data.get("data", [])
    if not dealer_turns:
        await handle_game_ending(message=message, game_service=game_service)
        return

    msg = await message.answer(text="Дилер берет карты до 17 очков.")
    await asyncio.sleep(1.5)

    final_turn = dealer_turns.pop()
    final_score = final_turn.get("score")
    final_cards = final_turn.get("cards")

    for turn in dealer_turns:
        score = turn.get("score")
        cards = turn.get("cards")
        await msg.edit_text(text=f"У дилера {score} очков\nКарты: {cards}")
        await asyncio.sleep(1.5)

    dealer_res_status = "перебор" if final_score and final_score > 21 else ""
    text = (
        f"У дилера {dealer_res_status}\n"
        f"Очки: {final_score}\n"
        f"Карты: {final_cards}.\n"
        f"Сейчас будут приведены результаты игры."
    )
    await msg.edit_text(text=text)
    await handle_game_ending(message=msg, game_service=game_service)


async def handle_dealer_reveal_action(
    dealer_action_data: dict[str, Any],
    message: Message,
    game_service: GameServiceTG,
):
    data = dealer_action_data.get("data", {})
    text = format_dealer_reveal_text(data)
    await message.answer(text)

    next_player_data = data.get("player")
    if next_player_data is not None:
        await pass_turn_next_player(
            message=message,
            player=next_player_data,
            game_service=game_service,
        )
    else:
        await handle_game_ending(message=message, game_service=game_service)


async def handle_game_ending(
    message: Message,
    game_service: GameServiceTG,
):
    res_data = await game_service.ending_game(message.chat.id)
    if res_data:
        text = format_ending_result_text(res_data)
        await message.answer(text)
    else:
        logger.warning(
            "No data received from ending_game for chat_id %r",
            message.chat.id,
        )
        await message.answer("Не удалось получить результаты игры.")


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


async def _handle_post_player_action(
    response_data: dict[str, Any],
    message: Message,
    game_service: GameServiceTG,
):
    next_player_data = response_data.get("next_player")
    if next_player_data is not None:
        await pass_turn_next_player(
            message=message,
            player=next_player_data,
            game_service=game_service,
        )
        return

    dealer_action_data = response_data.get("dealer_action")
    if dealer_action_data is not None:
        action_type = dealer_action_data.get("action")
        if action_type == "reveal":
            await handle_dealer_reveal_action(
                dealer_action_data=dealer_action_data,
                message=message,
                game_service=game_service,
            )
        elif action_type == "turns":
            await handle_dealer_turns(
                dealer_action_data=dealer_action_data,
                message=message,
                game_service=game_service,
            )
    else:
        logger.info(
            "Post player action for chat %r: No next player and no dealer action. Response data: %r",
            message.chat.id,
            response_data,
        )


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
        await _handle_post_player_action(response.data, callback.message, game_service)
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

    await _handle_post_player_action(response.data, callback.message, game_service)
