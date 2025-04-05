import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties

from src.infrastructure.config import settings
from src.infrastructure.telegram.bot import AiogramBot
from src.infrastructure.telegram.routers import routers
from src.infrastructure.redis_py.events.events_workerTG import EventWorkersTG
from src.infrastructure.redis_py.client import RedisSingleton
from src.infrastructure.repositories import RedisGameCacheRepo
from src.application.services import GameServiceTG
from src.utils.logger import setup_logger

logger = setup_logger(name=__name__, level=logging.INFO)

aiogrambot = AiogramBot(
    bot=Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(),
    ),
    storage=RedisStorage.from_url(str(settings.redis.url)),
)


def setup_game_workers():
    redis_ton = RedisSingleton()
    game_repo = RedisGameCacheRepo(redis=redis_ton)
    game_service = GameServiceTG(game_repo=game_repo)
    return EventWorkersTG(
        bot=aiogrambot.bot,
        game_service=game_service,
        redis=redis_ton,
    )


game_workers = setup_game_workers()


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    aiogrambot.dp.include_router(routers)
    tasks = await game_workers.start_workers()
    await asyncio.sleep(1)
    await aiogrambot.start_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
