from aiogram.filters import Filter
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, Message


class PlayerFilter(Filter):
    def __init__(self, lol):
        self.kek = lol

    async def __call__(
        self,
        callback: CallbackQuery,
    ) -> bool:
        cur_player_id = int(callback.data.split(":")[1])
        if cur_player_id != callback.from_user.id:
            await callback.answer("Не твой ход.")
            return False
        return True


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]):
        self.chat_types = chat_types

    async def __call__(
        self,
        event: Message | CallbackQuery,
    ):
        return event.chat.type in self.chat_types


class StandData(CallbackData, prefix="stand"):
    cur_player_id: int


class HitData(CallbackData, prefix="hit"):
    cur_player_id: int
