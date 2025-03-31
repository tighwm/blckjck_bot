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

aiogrambot = AiogramBot(
    bot=Bot(
        token=settings.bot.token,
        default=DefaultBotProperties(),
    ),
    storage=RedisStorage.from_url(str(settings.redis.url)),
)
redis_ton = RedisSingleton()
# lobby_repo = RedisLobbyCacheRepo(redis=redis_ton)
game_repo = RedisGameCacheRepo(redis=redis_ton)
game_service = GameServiceTG(game_repo=game_repo)
game_workers = EventWorkersTG(
    bot=aiogrambot.bot,
    game_service=game_service,
    redis=redis_ton,
    # lobby_repo=lobby_repo,
)


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
