import asyncio
from typing import Any, Callable, Coroutine, TypeVar
from functools import partial, wraps
from contextlib import asynccontextmanager

from redis.asyncio import Redis
from aiogram import Bot

from application.services import GameServiceTG
from application.services.timer_mng import timer_manager
from application.schemas import LobbySchema
from infrastructure.telegram.routers.utils import game_btns, format_player_info
from infrastructure.database.models.db_helper import db_helper
from infrastructure.repositories import RedisGameCacheRepo, SQLAlchemyUserRepository
from infrastructure.redis_py.redis_helper import redis_helper

T = TypeVar("T")
TaskFunc = Callable[..., Coroutine[Any, Any, T]]


@asynccontextmanager
async def game_service_getter(with_user_repo: bool = False):
    if with_user_repo:
        async with db_helper.session_getter() as session:
            user_repo = SQLAlchemyUserRepository(session=session)
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
                import traceback

                print(f"Error executing task: {e}")
                traceback.print_exc()

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
        await game_service.create_game(lobby_schema=lobby_schema)
        chat_id = lobby_schema.chat_id
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


class GameEndingListener(StreamListener):
    def __init__(
        self,
        redis: Redis,
        task_queue: TaskQueue,
        bot: Bot,
    ):
        super().__init__(redis, "game:ending", task_queue)
        self.bot = bot

    async def process_message(
        self,
        msg_id: bytes,
        data: dict[bytes, bytes],
    ):
        chat_id = int(data[b"chat_id"])

        await self.task_queue.add_task(
            self._result_of_end_game,
            chat_id=chat_id,
        )

    @with_game_service(True)
    async def _result_of_end_game(self, chat_id: int, game_service: GameServiceTG):
        response = await game_service.ending_game(chat_id)
        win_players = response.get("wins")
        push_players = response.get("push")
        lose_players = response.get("lose")

        text = ""
        if win_players:
            win_player_names = [player.get("player_name") for player in win_players]
            text = text + f"Выиграли у крупье: {', '.join(win_player_names)}\n"
        if push_players:
            push_player_names = [player.get("player_name") for player in push_players]
            text = text + f"В ничью сыграли: {', '.join(push_player_names)}\n"
        if lose_players:
            lose_player_names = [player.get("player_name") for player in lose_players]
            text = text + f"Проиграли ставку: {', '.join(lose_player_names)}"

        await self.bot.send_message(chat_id=chat_id, text=text)


class GameDealerListener(StreamListener):
    def __init__(
        self,
        redis: Redis,
        task_queue: TaskQueue,
        bot: Bot,
    ):
        super().__init__(redis, "game:dealer", task_queue)
        self.bot = bot

    async def process_message(
        self,
        msg_id: bytes,
        data: dict[bytes, bytes],
    ):
        chat_id = int(data[b"chat_id"])
        action = data[b"action"].decode("utf-8")

        await asyncio.sleep(1)
        if action == "reveal":
            await self.task_queue.add_task(self._dealer_reveal_secret, chat_id=chat_id)
        elif action == "turns":
            await self.task_queue.add_task(self._dealer_make_turns, chat_id=chat_id)

    @with_game_service(False)
    async def _dealer_reveal_secret(
        self,
        chat_id: int,
        game_service: GameServiceTG,
    ):
        # получаем данные дилера и неявно инициализируем второй круг ходов для игры
        response = await game_service.dealer_reveal_secret(chat_id)
        dealer = response.get("dealer")
        dealer_text = (
            f"Дилер раскрывает вторую карту...\n"
            f"Первая: {dealer.get("first_card")}\n"
            f"Вторая: ***\n"
            f"Очки: {dealer.get("score")}"
        )
        msg = await self.bot.send_message(chat_id=chat_id, text=dealer_text)

        # (не)красиво расскрываем вторую карту дилера
        secret_card = dealer.get("secret_card")
        effects = ["**", "*", secret_card]
        score = dealer.get("score")
        score_with_secret = dealer.get("score_with_secret")
        for eff in effects:
            await asyncio.sleep(1)
            view_score = score if eff != secret_card else score_with_secret
            dealer_text = (
                f"Дилер раскрывает вторую карту...\n"
                f"Первая: {dealer.get("first_card")}\n"
                f"Вторая: {eff}\n"
                f"Очки: {view_score}"
            )
            await msg.edit_text(text=dealer_text)

        # если у дилера блекджек - запускаем событие приведения результатов игры
        if score_with_secret == 21:
            await msg.answer("У дилера блекджек, все сосут. Доделать конец игры надо.")
            return
            # await self.game_service.ending_game(chat_id)

        player = response.get("player")
        if player is None:
            await msg.answer("эх.")
            # дернуть взятие карт дилера, раз нет следующего игрока на ход.
            await game_service.game_repo.push_dealer(chat_id, "turns")
            return
        player_id = player.get("player_id")
        msg = await msg.answer(
            text=format_player_info(player_data=player),
            reply_markup=game_btns(player_id),
        )
        timer_manager.create_timer(
            "game:turn",
            chat_id,
            game_service.kick_afk,
            player_id,
            30,
            msg,
        )

    @with_game_service(False)
    async def _dealer_make_turns(
        self,
        chat_id: int,
        game_service: GameServiceTG,
    ):
        # получаем ходы дилера от сервиса игр
        dealer_turns: list[dict] = await game_service.dealer_turns(chat_id)
        if not dealer_turns:
            await game_service.game_repo.push_ending(chat_id)
            return
        msg = await self.bot.send_message(
            chat_id=chat_id, text="Дилер берет карты до 17 очков."
        )
        await asyncio.sleep(1.5)

        # отправляем каждый ход (без последнего) дилера в чат
        final_turn = dealer_turns.pop()
        final_score = final_turn.get("score")
        final_cards = final_turn.get("cards")
        for turn in dealer_turns:
            score = turn.get("score")
            cards = turn.get("cards")
            await msg.edit_text(text=f"У дилера {score} очков\nКарты: {cards}")
            await asyncio.sleep(1.5)

        # уведомляем последний ход дилера
        dealer_res = ""
        if final_score > 21:
            dealer_res = "перебор"
        text = (
            f"У дилера {dealer_res}\n"
            f"Очки: {final_score}\n"
            f"Карты: {final_cards}.\n"
            f"Сейчас будут приведены результаты игры (нет)"
        )
        await msg.edit_text(text=text)

        await game_service.game_repo.push_ending(chat_id)


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
        self.listeners.append(
            GameDealerListener(
                self.redis,
                self.task_queue,
                self.bot,
            )
        )
        self.listeners.append(
            GameEndingListener(
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
