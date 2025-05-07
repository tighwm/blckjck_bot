from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from application.services import GameServiceTG
from application.services.timer_mng import timer_manager
from domain.types.game import SuccessType
from infrastructure.telegram.routers.states import ChatState
from infrastructure.telegram.routers.utils import game_btns
from infrastructure.telegram.middlewares import GameServiceGetter, AntiFlood


router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(GameServiceGetter())

# Регулярное выражение для фильтрации ставок от 1 и без чувствительности к регистру
filters_on_bid = F.text.regexp(r"(?i)^ставка\s([1-9]\d*)$")


def format_dealer_text(dealer_data: dict) -> str:
    return (
        f"Карты дилера\n"
        f"Первая: {dealer_data.get("first_card")}\n"
        f"Вторая: ***\n"
        f"Очки: {dealer_data.get("score")}"
    )


@router.message(filters_on_bid, ChatState.bid)
async def bid_handle(
    message: Message,
    state: FSMContext,
    game_service: GameServiceTG,
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
        player = response.data.get("player")
        player_id = player.get("player_id")
        dealer_text = format_dealer_text(response.data.get("dealer"))
        await message.answer(text=dealer_text)
        msg = await message.answer(
            text=f"Ход игрока {player.get("player_name")}",
            reply_markup=game_btns(player_id),
        )
        timer_manager.create_timer(
            "game:turn",
            msg.chat.id,
            game_service.kick_afk,
            player_id,
            30,
            msg,
        )
