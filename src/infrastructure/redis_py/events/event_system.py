import asyncio
from typing import Any, Callable, Coroutine, TypeVar
from functools import partial

from redis.asyncio import Redis
from aiogram import Bot
from aiogram.types import Message

from src.application.services import GameServiceTG
from src.application.schemas import LobbySchema


T = TypeVar("T")
TaskFunc = Callable[..., Coroutine[Any, Any, T]]


class TaskQueue:
    """Очередь асинхронных задач"""

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
                print(f"Error executing task: {e}")

    async def start(self):
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self.worker())
            self.workers.append(worker)
        return self.workers


class StreamListener:
    """Слушатель потока событий Redis"""

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
        """Абстрактный метод обработки сообщения"""
        raise NotImplementedError

    async def run(self):
        while True:
            try:
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

            except Exception as e:
                print(f"Error in {self.__class__.__name__}: {e}")
                await asyncio.sleep(1)


class GameStartingListener(StreamListener):
    """Слушатель событий начала игры"""

    def __init__(
        self,
        redis: Redis,
        task_queue: TaskQueue,
        game_service: GameServiceTG,
        bot: Bot,
    ):
        super().__init__(redis, "game:starting", task_queue)
        self.game_service = game_service
        self.bot = bot

    async def process_message(
        self,
        msg_id: bytes,
        data: dict[bytes, bytes],
    ):
        lobby_json_str = data[b"lobby_data"]
        message_json_str = data[b"message"]

        lobby_schema = LobbySchema.model_validate_json(lobby_json_str)
        message = Message.model_validate_json(message_json_str)

        # Добавляем задачу создания игры в очередь
        await self.task_queue.add_task(
            self._create_game_task, lobby_schema=lobby_schema, message=message
        )

    async def _create_game_task(
        self,
        lobby_schema: LobbySchema,
        message: Message,
    ):
        """Задача создания игры"""
        await self.game_service.create_game(lobby_schema=lobby_schema)
        msg = await message.answer(text="Делайте ставки к началу игры.").as_(self.bot)

        # Создаем таску таймера
        task = asyncio.create_task(
            self.game_service.bid_timer(message=msg),
        )
        GameServiceTG.save_timer_task(
            key=str(message.chat.id),
            task=task,
        )


class GameDealerListener(StreamListener):
    """Слушатель событий дилера игры"""

    def __init__(
        self,
        redis: Redis,
        task_queue: TaskQueue,
        game_service: GameServiceTG,
        bot: Bot,
    ):
        super().__init__(redis, "game:dealer", task_queue)
        self.game_service = game_service
        self.bot = bot

    async def process_message(
        self,
        msg_id: bytes,
        data: dict[bytes, bytes],
    ):
        pass

    async def _dealer_turn(self, message: Message):
        pass


class EventSystemTG:
    """Система обработки событий для Telegram игр"""

    def __init__(
        self,
        bot: Bot,
        game_service: GameServiceTG,
        redis: Redis,
        max_workers: int = 5,
    ):
        self.bot = bot
        self.game_service = game_service
        self.redis = redis

        # Создаем очередь задач
        self.task_queue = TaskQueue(max_workers=max_workers)

        # Создаем слушателей
        self.listeners: list[StreamListener] = []
        self._create_listeners()

    def _create_listeners(self):
        """Создание всех слушателей потоков"""
        self.listeners.append(
            GameStartingListener(
                self.redis, self.task_queue, self.game_service, self.bot
            )
        )
        # self.listeners.append(
        #     GameDealerListener(self.redis, self.task_queue, self.game_service, self.bot)
        # )

    async def start(self):
        """Запуск системы обработки событий"""
        # Запускаем очередь задач
        worker_tasks = await self.task_queue.start()

        # Запускаем всех слушателей
        listener_tasks = [
            asyncio.create_task(listener.run()) for listener in self.listeners
        ]

        # Запускаем все задачи
        all_tasks = worker_tasks + listener_tasks
        await asyncio.gather(*all_tasks)
