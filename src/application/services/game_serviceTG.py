from enum import Enum, auto
from dataclasses import dataclass

from aiogram.types import Message

from application.interfaces import BaseTelegramUserRepo, CacheGameRepoInterface
from application.schemas import GameSchema, LobbySchema, UserPartial
from application.services.timer_mng import timer_manager
from domain.entities import Lobby, Game, Player
from domain.types.game.errors import PlayerNotFound, AnotherPlayerTurn
from infrastructure.telegram.routers.callback_handlers import handle_post_player_action


class ResponseType(Enum):
    BID_ACCEPTED = auto()
    BID_DENIED = auto()
    HIT_ACCEPTED = auto()
    STAND_ACCEPTED = auto()

    PLAYER_NOT_FOUND = auto()
    ANOTHER_PLAYER_TURN = auto()


@dataclass
class Response:
    success: bool
    type: ResponseType
    data: dict | None = None


def format_kicked_non_bid_players(players_data: list[dict]) -> str:
    if len(players_data) > 1:
        start_text = "Игроки "
        end_text = " исключены за бездействие"
    else:
        start_text = "Игрок "
        end_text = " исключен за бездействие"
    players_name = [player_data.get("player_name") for player_data in players_data]
    text = start_text + ", ".join(players_name) + end_text
    return text


class GameServiceTG:
    def __init__(
        self,
        game_repo: CacheGameRepoInterface,
        user_repo: BaseTelegramUserRepo | None = None,
    ):
        self.game_repo = game_repo
        self.user_repo = user_repo

    async def apply_players_amount(
        self,
        players: list[dict],
    ):
        if not players:
            return
        amounts = {player["player_id"]: player.get("amount") for player in players}
        users_list = await self.user_repo.get_users_by_tg_ids(
            tg_ids=list(amounts.keys())
        )
        users_update = {}
        for user in users_list:
            amount = amounts.get(user.tg_id)
            users_update[user] = UserPartial(balance=user.balance + amount)
        await self.user_repo.update_users(datas_update=users_update, partial=True)

    async def kick_afk(
        self,
        message: Message,
        player_id: int,
    ):
        chat_id = message.chat.id
        async with self.game_repo.with_lock(chat_id):
            game_schema = await self.game_repo.get_game(chat_id)
            if game_schema is None:
                return
            game = Game.from_dto(game_schema)
            res = game.set_out_for_player(player_id)
            player = res.get("player")

            await message.answer(
                f"Игрок {player.get("player_name")} исключен за бездействие."
            )
            await message.delete_reply_markup()

            await self.game_repo.cache_game(game)
            await handle_post_player_action(
                response_data=res,
                message=message,
                game_service=self,
            )

    async def bid_timer(
        self,
        message: Message,
    ):
        chat_id = message.chat.id
        async with self.game_repo.with_lock(chat_id):
            game_schema = await self.game_repo.get_game(chat_id)
            if game_schema is None:
                return
            game = Game.from_dto(game_schema)

            res = game.set_out_for_non_bid_players()
            out_players = res.get("out_players")
            if out_players:
                text = format_kicked_non_bid_players(players_data=out_players)
                await message.answer(text)

            if len(out_players) == len(game.players):
                await message.answer("Пиздец.")
                await self.game_repo.delete_cache_game(chat_id)
                return

            await handle_post_player_action(
                response_data=res,
                message=message,
                game_service=self,
            )
            await self.game_repo.set_game_state(chat_id)
            await self.game_repo.cache_game(game)

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
    ) -> Response | None:
        async with self.game_repo.with_lock(chat_id):
            game_schema = await self.game_repo.get_game(chat_id=chat_id)
            if not game_schema:
                return None

            user_model = await self.user_repo.get_user_by_tg_id(
                tg_id=user_tg_id,
                schema=False,
            )
            if bid > user_model.balance:
                return Response(
                    success=False,
                    type=ResponseType.BID_DENIED,
                )

            game = Game.from_dto(game_schema)
            try:
                res = game.player_bid(
                    player_id=user_tg_id,
                    bid=bid,
                )
            except PlayerNotFound:
                return Response(
                    success=False,
                    type=ResponseType.PLAYER_NOT_FOUND,
                )
            if res.get("all_bets"):
                timer_manager.cancel_timer(timer_type="game:bid", chat_id=chat_id)
                res["the_deal"] = game.the_deal()

            new_balance = user_model.balance - bid
            update_user = UserPartial(balance=new_balance)
            await self.user_repo.update_user(
                user=user_model,
                data_update=update_user,
                partial=True,
            )
            await self.game_repo.cache_game(game)
            return Response(
                success=True,
                type=ResponseType.BID_ACCEPTED,
                data=res,
            )

    async def player_turn_hit(
        self,
        chat_id: int,
        user_tg_id: int,
    ) -> Response | None:
        async with self.game_repo.with_lock(chat_id):
            timer_manager.cancel_timer(
                timer_type="game:turn",
                chat_id=chat_id,
                player_id=user_tg_id,
            )
            game_schema = await self.game_repo.get_game(chat_id=chat_id)
            if not game_schema:
                return None

            game = Game.from_dto(game_schema)
            try:
                res = game.player_hit(player_id=user_tg_id)
            except AnotherPlayerTurn:
                return Response(
                    success=False,
                    type=ResponseType.ANOTHER_PLAYER_TURN,
                )
            except PlayerNotFound:
                return Response(
                    success=False,
                    type=ResponseType.PLAYER_NOT_FOUND,
                )

            await self.game_repo.cache_game(game)
            return Response(
                success=True,
                type=ResponseType.HIT_ACCEPTED,
                data=res,
            )

    async def player_turn_stand(
        self,
        chat_id: int,
        user_tg_id: int,
    ) -> Response | None:
        async with self.game_repo.with_lock(chat_id):
            timer_manager.cancel_timer(
                timer_type="game:turn",
                chat_id=chat_id,
                player_id=user_tg_id,
            )
            game_schema = await self.game_repo.get_game(chat_id=chat_id)
            if not game_schema:
                return None

            game = Game.from_dto(game_schema)
            try:
                res = game.player_stand(player_id=user_tg_id)
            except AnotherPlayerTurn:
                return Response(
                    success=False,
                    type=ResponseType.ANOTHER_PLAYER_TURN,
                )
            except PlayerNotFound:
                return Response(
                    success=False,
                    type=ResponseType.PLAYER_NOT_FOUND,
                )

            await self.game_repo.cache_game(game)
            return Response(
                success=True,
                type=ResponseType.STAND_ACCEPTED,
                data=res,
            )

    async def dealer_reveal_secret(
        self,
        chat_id: int,
    ):
        async with self.game_repo.with_lock(chat_id):
            game_schema = await self.game_repo.get_game(chat_id=chat_id)
            if not game_schema:
                return None

            game = Game.from_dto(game_schema)

            res = game.init_second_round()
            await self.game_repo.cache_game(game)

            return res

    async def dealer_turns(self, chat_id: int):
        async with self.game_repo.with_lock(chat_id):
            game_schema = await self.game_repo.get_game(chat_id=chat_id)
            if not game_schema:
                return None

            game = Game.from_dto(game_schema)

            res = game.dealer_turns()

            await self.game_repo.cache_game(game)

            return res

    async def ending_game(self, chat_id: int):
        async with self.game_repo.with_lock(chat_id):
            game_schema = await self.game_repo.get_game(chat_id)
            if not game_schema:
                return None

            game = Game.from_dto(game_schema)
            res = game.result_of_game()
            wins = res.get("wins")
            push = res.get("push")

            players = wins + push
            await self.apply_players_amount(players=players)

            await self.game_repo.delete_cache_game(chat_id)
            return res
