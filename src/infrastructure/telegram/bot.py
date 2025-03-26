from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.strategy import FSMStrategy


class AiogramBot:
    def __init__(
        self,
        bot: Bot,
        storage: (
            BaseStorage | MemoryStorage | RedisStorage | MongoStorage | None
        ) = None,
    ):
        self.bot = bot
        self.storage = storage
        self.dp = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.CHAT)

    async def start_polling(self):
        await self.dp.start_polling(self.bot)
