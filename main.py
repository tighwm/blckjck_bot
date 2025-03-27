import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties

from src.infrastructure.config import settings
from src.infrastructure.telegram.bot import AiogramBot
from src.infrastructure.telegram.routers import routers

bot = AiogramBot(
    bot=Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(),
    ),
    storage=RedisStorage.from_url(str(settings.redis.url)),
)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot.dp.include_router(routers)
    await bot.start_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
