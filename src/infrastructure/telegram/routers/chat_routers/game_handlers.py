from typing import TYPE_CHECKING
import asyncio

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from domain.types.game import SuccessType
from infrastructure.telegram.routers.states import ChatState
from utils.tg.filters import ChatTypeFilter
from utils.tg.functions import pass_turn_next_player
from infrastructure.telegram.middlewares import GameServiceGetter, AntiFlood

if TYPE_CHECKING:
    from application.services import GameServiceTG

router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(GameServiceGetter())

# Регулярное выражение для фильтрации ставок от 1 и без чувствительности к регистру
filters_on_bid = F.text.regexp(r"(?i)^ставка\s([1-9]\d*)$")


def format_dealer_cards_text(dealer_data: dict) -> str:
    return (
        f"Карты дилера\n"
        f"Первая: {dealer_data.get("first_card")}\n"
        f"Вторая: ***\n"
        f"Очки: {dealer_data.get("score")}"
    )


async def the_deal_process(
    message: Message,
    deal_data: list[dict],
):
    await message.answer("Первая раздача карт игрокам.")
    for player in deal_data:
        text = (
            f"Карты игрока {player.get("player_name")}\n"
            f"{player.get("cards")} {"" if player.get("result") is None else " Блекджек💀"}\n"
            f"Очки: {player.get("score")}\n"
        )
        await message.answer(text)
        await asyncio.sleep(1)


@router.message(
    ChatTypeFilter(["group", "supergroup"]),
    filters_on_bid,
    ChatState.bid,
)
async def bid_handle(
    message: Message,
    state: FSMContext,
    game_service: "GameServiceTG",
):
    user_bid = int(message.text.split()[1])  # Получаем ставку из "ставка (число)"
    if user_bid < 5:
        await message.answer("Ставка не дожна быть менее 5")
        return

    response = await game_service.player_set_bid(
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        bid=user_bid,
    )
    if response is None:
        await message.answer("Копейки пересчитай свои.")
        return

    if response.type == SuccessType.BID_ACCEPTED:
        await message.answer("Ставка принята.")
    elif response.type == SuccessType.ALL_PLAYERS_BET:
        await state.set_state(ChatState.game)

        await the_deal_process(message, response.data.get("the_deal"))

        dealer_text = format_dealer_cards_text(response.data.get("dealer"))
        await message.answer(text=dealer_text)

        player = response.data.get("player")
        await pass_turn_next_player(message, player, game_service)
