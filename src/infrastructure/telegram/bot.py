from aiogram import Bot, Dispatcher

from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy


class AiogramBot:
    def __init__(
        self,
        bot: Bot,
        storage: RedisStorage | None = None,
    ):
        self.bot = bot
        self.storage = storage
        self.dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.CHAT)

    async def start_polling(self):
        await self.dp.start_polling(self.bot)
