from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.redis import RedisStorage

from src.infrastructure.config import settings


class TelegramBot:
    def __init__(self):
        self.bot = Bot(
            token=settings.bot.token,
            default=DefaultBotProperties(),
        )
        self.storage = RedisStorage.from_url(str(settings.redis.url))
        self.dp = Dispatcher(storage=self.storage, fsm_strategy=FSMStrategy.CHAT)

    async def start_polling(self):
        await self.dp.start_polling(self.bot)
