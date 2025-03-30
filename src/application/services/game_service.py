from dataclasses import asdict

from src.application.schemas import GameSchema, LobbySchema
from src.application.interfaces import CacheGameRepoInterface
from src.domain.entities import Lobby, Game, Player


class GameService:
    def __init__(
        self,
        game_repo=CacheGameRepoInterface,
    ):
        self.game_repo = game_repo

    async def create_game(
        self,
        lobby_schema: LobbySchema,
    ) -> GameSchema | None:
        lobby = Lobby(**lobby_schema.model_dump())
        players = {user.tg_id: Player(**asdict(user)) for user in lobby.users}
        game = Game(
            chat_id=lobby.chat_id,
            players=players,
        )
        game_schema = await self.game_repo.cache_game(game=game)
        if not game_schema:
            return None

        return game_schema
