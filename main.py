import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties

from src.infrastructure.config import settings
from src.infrastructure.telegram.bot import AiogramBot
from src.infrastructure.telegram.routers import routers
from src.infrastructure.redis_py.events.event_system import EventSystemTG
from src.infrastructure.redis_py.client import RedisSingleton
from src.utils.logger import setup_logger

logger = setup_logger(name=__name__, level=logging.INFO)

fsm_redis_storage = RedisStorage.from_url(str(settings.redis.url))

aiogrambot = AiogramBot(
    bot=Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(),
    ),
    storage=fsm_redis_storage,
)

tg_event_sys = EventSystemTG(
    bot=aiogrambot.bot,
    redis=RedisSingleton(),
)


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    aiogrambot.dp.include_router(routers)
    event_sys_task = asyncio.create_task(tg_event_sys.start())
    await asyncio.sleep(1)
    await aiogrambot.start_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
