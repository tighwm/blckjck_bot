import asyncio
import logging
from typing import TYPE_CHECKING, Any

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


logger = logging.getLogger(__name__)


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


async def handle_post_player_action(
    response_data: dict[str, Any],
    message: Message,
    game_service: "GameServiceTG",
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


async def handle_dealer_turns(
    dealer_action_data: dict[str, Any],
    message: Message,
    game_service: "GameServiceTG",
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
    game_service: "GameServiceTG",
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
    game_service: "GameServiceTG",
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
