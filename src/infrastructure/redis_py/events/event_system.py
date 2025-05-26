import asyncio
import logging
from typing import Any, Callable, Coroutine, TypeVar
from functools import partial, wraps
from contextlib import asynccontextmanager

from redis.asyncio import Redis
from aiogram import Bot

from application.services import GameServiceTG
from application.services.timer_mng import timer_manager
from application.schemas import LobbySchema
from infrastructure.database.models.db_helper import db_helper
from infrastructure.repositories import RedisGameCacheRepo, SQLAlchemyUserRepositoryTG
from infrastructure.redis_py.redis_helper import redis_helper

T = TypeVar("T")
TaskFunc = Callable[..., Coroutine[Any, Any, T]]

logger = logging.getLogger(__name__)


@asynccontextmanager
async def game_service_getter(with_user_repo: bool = False):
    if with_user_repo:
        async with db_helper.ctx_session_getter() as session:
            user_repo = SQLAlchemyUserRepositoryTG(session=session)
            game_repo = RedisGameCacheRepo(redis=redis_helper.get_redis_client())
            game_service = GameServiceTG(game_repo=game_repo, user_repo=user_repo)
            yield game_service
    else:
        game_repo = RedisGameCacheRepo(redis=redis_helper.get_redis_client())
        game_service = GameServiceTG(game_repo=game_repo)
        yield game_service


def with_game_service(with_user_repo: bool):
    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with game_service_getter(with_user_repo) as game_service:
                return await func(*args, game_service=game_service, **kwargs)

        return wrapper

    return decorator


class TaskQueue:
    def __init__(self, max_workers: int = 5):
        self.queue = asyncio.Queue()
        self.max_workers = max_workers
        self.workers = []

    async def add_task(self, func: TaskFunc, *args, **kwargs):
        task = partial(func, *args, **kwargs)
        await self.queue.put(task)

    async def worker(self):
        while True:
            try:
                task_func = await self.queue.get()
                await task_func()
                self.queue.task_done()
            except Exception as e:
                logger.error(
                    "Error executing task: %s\n%r",
                    e,
                )

    async def start(self):
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self.worker())
            self.workers.append(worker)
        return self.workers


class StreamListener:
    def __init__(
        self,
        redis: Redis,
        stream_key: str,
        task_queue: TaskQueue,
    ):
        self.redis = redis
        self.stream_key = stream_key
        self.task_queue = task_queue

    async def process_message(
        self,
        msg_id: bytes,
        data: dict[bytes, bytes],
    ):
        raise NotImplementedError

    async def run(self):
        while True:
            stream = await self.redis.xread(
                streams={self.stream_key: "$"},
                count=1,
                block=0,
            )
            if not stream:
                continue

            stream_name, messages = next(iter(stream.items()))
            msg_id, data = messages[0][0]

            await self.process_message(msg_id, data)

            await self.redis.xdel(stream_name, msg_id)


class GameStartingListener(StreamListener):
    def __init__(
        self,
        redis: Redis,
        task_queue: TaskQueue,
        bot: Bot,
    ):
        super().__init__(redis, "game:starting", task_queue)
        self.bot = bot

    async def process_message(
        self,
        msg_id: bytes,
        data: dict[bytes, bytes],
    ):
        lobby_json_str = data[b"lobby_data"]

        lobby_schema = LobbySchema.model_validate_json(lobby_json_str)

        await self.task_queue.add_task(
            self._create_game_task,
            lobby_schema=lobby_schema,
        )

    @with_game_service(False)
    async def _create_game_task(
        self,
        game_service: GameServiceTG,
        lobby_schema: LobbySchema,
    ):
        chat_id = lobby_schema.chat_id
        if not lobby_schema.users:
            await self.bot.send_message(
                chat_id=chat_id,
                text="Нет игроков для начала игры.",
            )
            await self.redis.delete(f"fsm:{chat_id}:{chat_id}:state")
            return
        await game_service.create_game(lobby_schema=lobby_schema)
        msg = await self.bot.send_message(
            chat_id=chat_id,
            text="Делайте ставки к началу игры.",
        )
        timer_manager.create_timer(
            "game:bid",
            chat_id,
            game_service.bid_timer,
            None,
            30,
            msg,
        )


class EventSystemTG:
    def __init__(
        self,
        bot: Bot,
        redis: Redis,
        max_workers: int = 5,
    ):
        self.bot = bot
        self.redis = redis

        # Создаем очередь задач
        self.task_queue = TaskQueue(max_workers=max_workers)

        # Создаем слушателей
        self.listeners: list[StreamListener] = []
        self._create_listeners()

    def _create_listeners(self):
        self.listeners.append(
            GameStartingListener(
                self.redis,
                self.task_queue,
                self.bot,
            )
        )

    async def start(self):
        # Запускаем очередь задач
        worker_tasks = await self.task_queue.start()

        # Запускаем всех слушателей
        listener_tasks = [
            asyncio.create_task(listener.run()) for listener in self.listeners
        ]

        # Запускаем все задачи
        all_tasks = worker_tasks + listener_tasks
        await asyncio.gather(*all_tasks)
