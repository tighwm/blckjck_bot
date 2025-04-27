from redis.asyncio import Redis

from src.application.interfaces.cache_game_repo_interface import CacheGameRepoInterface
from src.domain.entities.game import Game
from src.application.schemas.game import GameSchema


class RedisGameCacheRepo(CacheGameRepoInterface):
    def __init__(
        self,
        redis: Redis,
        key_prefix: str = "Game",
        dealer_stream_key: str = "game:dealer",
        ending_stream_key: str = "game:ending",
    ):
        self.redis = redis
        self.key_prefix = key_prefix
        self.dealer_stream_key = dealer_stream_key
        self.ending_stream_key = ending_stream_key

    def _get_key(self, chat_id: int) -> str:
        return f"{self.key_prefix}:{chat_id}"

    async def cache_game(
        self,
        game: Game,
        exp: int | None = None,
    ) -> GameSchema:
        game_schema = GameSchema.model_validate(game, from_attributes=True)
        key = self._get_key(game_schema.chat_id)

        await self.redis.set(
            name=key,
            value=game_schema.model_dump_json(),
            ex=exp,
        )

        return game_schema

    async def get_game(
        self,
        chat_id: int,
    ) -> GameSchema | None:
        key = self._get_key(chat_id)
        data = await self.redis.get(key)
        if not data:
            return None

        game_schema = GameSchema.model_validate_json(data)
        return game_schema

    async def delete_cache_game(self, chat_id: int) -> None:
        fsm_key = f"fsm:{chat_id}:{chat_id}:state"
        await self.redis.delete(fsm_key)
        key = self._get_key(chat_id)
        await self.redis.delete(key)

    async def set_game_state(self, chat_id: int):
        fsm_key = f"fsm:{chat_id}:{chat_id}:state"
        await self.redis.set(name=fsm_key, value="ChatState:game")

    async def push_dealer(self, chat_id: int, action: str):
        await self.redis.xadd(
            name=self.dealer_stream_key,
            fields={
                "chat_id": str(chat_id),
                "action": action,
            },
        )

    async def push_ending(self, chat_id: int):
        await self.redis.xadd(
            name=self.ending_stream_key,
            fields={"chat_id": str(chat_id)},
        )
