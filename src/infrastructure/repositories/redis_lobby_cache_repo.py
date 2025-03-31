from redis.asyncio import Redis
from aiogram.types import Message

from src.application.interfaces.cache_lobby_repo_interface import (
    CacheLobbyRepoInterface,
)
from src.domain.entities.lobby import Lobby
from src.application.schemas.lobby import LobbySchema


class RedisLobbyCacheRepo(CacheLobbyRepoInterface):
    def __init__(
        self,
        redis: Redis,
        key_prefix: str = "Lobby",
        stream_key: str = "game:starting",
    ):
        self.redis = redis
        self.key_prefix = key_prefix
        self.stream_key = stream_key

    def _get_key(
        self,
        chat_id: int,
    ):
        return f"{self.key_prefix}:{chat_id}"

    async def cache_lobby(
        self,
        lobby: Lobby,
        exp: int = 180,
    ) -> LobbySchema:
        key = self._get_key(lobby.chat_id)
        lobby_schema = LobbySchema.model_validate(lobby, from_attributes=True)

        await self.redis.set(
            name=key,
            value=lobby_schema.model_dump_json(),
            ex=None,
        )

        return lobby_schema

    async def get_lobby(
        self,
        chat_id: int,
    ) -> LobbySchema | None:
        key = self._get_key(chat_id)
        data = await self.redis.get(key)
        if not data:
            return None
        lobby_schema = LobbySchema.model_validate_json(data)
        return lobby_schema

    async def delete_lobby(
        self,
        chat_id: int,
    ):
        key = self._get_key(chat_id)
        await self.redis.delete(key)

    async def exists_lobby(
        self,
        chat_id: int,
    ):
        key = self._get_key(chat_id)
        return await self.redis.exists(key)


class RedisLobbyCacheRepoTG(RedisLobbyCacheRepo):
    async def push_starting(
        self,
        chat_id: int,
        message: Message,
    ):
        key = self._get_key(chat_id)
        data = await self.redis.get(key)
        if not data:
            return None

        await self.redis.xadd(
            name=self.stream_key,
            fields={
                "lobby_data": data,
                "message": message.model_dump_json(),
            },
        )
