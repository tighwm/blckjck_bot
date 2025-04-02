from enum import Enum

from src.application.schemas import GameSchema, LobbySchema, UserPartial
from src.infrastructure.repositories import RedisGameCacheRepo, SQLAlchemyUserRepository
from src.domain.entities import Lobby, Game, Player
from src.domain.types.game import GameResult, ErrorType, SuccessType


class GameServiceTG:
    def __init__(
        self,
        user_repo: SQLAlchemyUserRepository,
        game_repo: RedisGameCacheRepo,
    ):
        self.game_repo = game_repo
        self.user_repo = user_repo

    async def create_game(
        self,
        lobby_schema: LobbySchema,
    ) -> GameSchema | None:
        lobby = Lobby.from_dto(lobby_schema)
        players = {
            user.tg_id: Player(username=user.username, tg_id=user.tg_id)
            for user in lobby.users
        }
        game = Game(
            chat_id=lobby.chat_id,
            players=players,
        )
        game_schema = await self.game_repo.cache_game(game=game)
        if not game_schema:
            return None

        return game_schema

    async def player_set_bid(
        self,
        chat_id: int,
        user_tg_id: int,
        bid: int,
    ):
        game_schema = await self.game_repo.get_game(chat_id=chat_id)
        if not game_schema:
            return None

        user_model = await self.user_repo.get_user_by_tg_id(
            tg_id=user_tg_id,
            schema=False,
        )
        if bid > user_model.balance:
            return None

        game = Game.from_dto(game_schema)
        res = game.player_bid(
            player_id=user_tg_id,
            bid=bid,
        )
        if not res.success:
            return res

        new_balance = user_model.balance - bid
        update_user = UserPartial(balance=new_balance)
        await self.user_repo.update_user(
            user=user_model,
            data_update=update_user,
            partial=True,
        )
        await self.game_repo.cache_game(game)
        return res
