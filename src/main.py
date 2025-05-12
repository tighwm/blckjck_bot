import asyncio
import logging

from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties

from infrastructure.config import settings
from infrastructure.telegram.bot import AiogramBot
from infrastructure.telegram.routers import routers
from infrastructure.redis_py.events.event_system import EventSystemTG
from infrastructure.redis_py.redis_helper import redis_helper

from utils.logger import configure_logger

fsm_redis_storage = RedisStorage.from_url(str(settings.redis.url))

logger = logging.getLogger(__name__)

aiogram_bot = AiogramBot(
    bot=Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(),
    ),
    storage=fsm_redis_storage,
)

tg_event_sys = EventSystemTG(
    bot=aiogram_bot.bot,
    redis=redis_helper.get_redis_client(),
)


async def main():
    configure_logger(filename="bot-logs/bot.log", level=logging.WARNING)
    logger.info("Logger was configured.")
    aiogram_bot.dp.include_router(routers)
    event_sys_task = asyncio.create_task(tg_event_sys.start())
    await asyncio.sleep(1)
    await aiogram_bot.start_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
