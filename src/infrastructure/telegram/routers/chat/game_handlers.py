from typing import TYPE_CHECKING

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from application.services.serv_types import ResponseType
from infrastructure.telegram.routers.states import ChatState
from utils.tg.filters import ChatTypeFilter
from utils.tg.functions import pass_turn_next_player
from infrastructure.telegram.middlewares import GameServiceGetter, AntiFlood, SaveUserDB

if TYPE_CHECKING:
    from application.services import GameServiceTG

router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(SaveUserDB())
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


def text_deal_process(
    data: dict,
) -> str:
    deal_data = data.get("the_deal")
    text = "Первая раздача карт игрокам.\n"
    for player in deal_data:
        text += (
            f"Карты игрока {player.get("player_name")}\n"
            f"{player.get("cards")} {"" if player.get("result") is None else " Блекджек💀"}\n"
            f"Очки: {player.get("score")}\n \n"
        )
    dealer_text = format_dealer_cards_text(data.get("dealer"))
    text += dealer_text
    return text


async def process_not_success(
    message: Message,
    err_type: ResponseType,
):
    if err_type == ResponseType.BID_DENIED:
        await message.answer("Копейки пересчитай /profile")
    elif err_type == ResponseType.PLAYER_NOT_FOUND:
        await message.answer("Ты не в игре.")


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
        await message.answer("Ставка не должна быть менее 5")
        return

    response = await game_service.player_set_bid(
        chat_id=message.chat.id,
        user_tg_id=message.from_user.id,
        bid=user_bid,
    )
    if response is None:
        return await message.answer("Response is None.")
    elif response.success is False:
        await process_not_success(message, response.type)

    if response.type == ResponseType.BID_ACCEPTED:
        await message.answer("Ставка принята.")
    if response.data.get("all_bets"):
        await state.set_state(ChatState.game)

        text = text_deal_process(response.data)
        await message.answer(text=text)

        player = response.data.get("player")
        await pass_turn_next_player(message, player, game_service)
