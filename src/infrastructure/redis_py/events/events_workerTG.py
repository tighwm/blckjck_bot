import asyncio

from redis.asyncio import Redis
from aiogram import Bot
from aiogram.types import Message

from src.application.services import GameServiceTG
from src.application.schemas import LobbySchema
from src.application.interfaces import CacheLobbyRepoInterface


class EventWorkersTG:
    def __init__(
        self,
        bot: Bot,
        game_service: GameServiceTG,
        # lobby_repo: CacheLobbyRepoInterface,
        redis: Redis,
    ):
        self.bot = bot
        self.game_service = game_service
        self.redis = redis
        # self.lobby_repo = lobby_repo
        self.stream_timer_key = "game:timer"
        self.stream_starting_key = "game:starting"
        self.stream_lobby_timer_key = "lobby:timer"

    async def start_workers(self):
        # worker1 = asyncio.create_task(self.game_timer_worker(self))
        worker2 = asyncio.create_task(self.game_starting_worker())

        return worker2

    async def game_timer_worker(self):
        pass

    async def game_starting_worker(self):
        while True:
            stream = await self.redis.xread(
                streams={self.stream_starting_key: "$"},
                count=1,
                block=0,
            )
            if not stream:
                continue

            stream_name, messages = next(iter(stream.items()))
            data = messages[0][0][1]
            lobby_json_str = data[b"lobby_data"]
            message_json_str = data[b"message"]

            lobby_schema = LobbySchema.model_validate_json(lobby_json_str)
            message = Message.model_validate_json(message_json_str)
            await message.answer("Пошел нахуй.").as_(self.bot)

    # async def lobby_timer(self):
    #     while True:
    #         stream = await self.redis.xread(
    #             streams={self.stream_lobby_timer_key: "$"},
    #             count=1,
    #             block=200,
    #         )
    #         if not stream:
    #             continue

    #         stream_name, messages = next(iter(stream.items()))
    #         data = messages[0][0][1]
