import asyncio

from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties

from infrastructure.config import settings
from infrastructure.telegram.bot import AiogramBot
from infrastructure.telegram.routers import routers
from infrastructure.redis_py.events.event_system import EventSystemTG
from infrastructure.redis_py.client import RedisSingleton
from utils.logger import setup_logger

logger = setup_logger(name=__name__, log_file="logs/.log", level="info", detailed=True)

fsm_redis_storage = RedisStorage.from_url(str(settings.redis.url))

aiogram_bot = AiogramBot(
    bot=Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(),
    ),
    storage=fsm_redis_storage,
)

tg_event_sys = EventSystemTG(
    bot=aiogram_bot.bot,
    redis=RedisSingleton(),
)


async def main():
    aiogram_bot.dp.include_router(routers)
    await asyncio.create_task(tg_event_sys.start())
    await asyncio.sleep(1)
    await aiogram_bot.start_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
