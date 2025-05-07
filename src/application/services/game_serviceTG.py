import logging
from typing import Any

from aiogram.types import Message

from application.schemas import GameSchema, LobbySchema, UserPartial
from application.services.timer_mng import timer_manager
from infrastructure.repositories import RedisGameCacheRepo, SQLAlchemyUserRepository
from domain.entities import Lobby, Game, Player, PlayerResult
from domain.types.game import SuccessType, GameResult
from infrastructure.telegram.routers.utils import game_btns

logger = logging.getLogger(__name__)


async def update_users_balance(
    user_repo: SQLAlchemyUserRepository,
    players: list[dict],
):
    if not players:
        return
    amounts = {player["player_id"]: player.get("amount") for player in players}
    users_list = await user_repo.get_users_by_tg_ids(tg_ids=list(amounts.keys()))
    users_update = {}
    for user in users_list:
        amount = amounts.get(user.tg_id)
        users_update[user] = UserPartial(balance=user.balance + amount)
    await user_repo.update_users(datas_update=users_update, partial=True)


class GameServiceTG:
    def __init__(
        self,
        game_repo: RedisGameCacheRepo,
        user_repo: SQLAlchemyUserRepository | None = None,
    ):
        self.game_repo = game_repo
        self.user_repo = user_repo

    async def kick_afk(
        self,
        message: Message,
    ):
        chat_id = message.chat.id
        game_schema = await self.game_repo.get_game(chat_id)
        if game_schema is None:
            return
        game = Game.from_dto(game_schema)

        player = game.get_current_turn_player()
        player.result = PlayerResult.OUT
        await message.answer(f"Игрок {player.username} исключен за бездействие.")

        next_player = game.next_player()
        if next_player is None:
            await message.answer(f"Ход переходит дилеру")
            action = "reveal" if game.current_round == 2 else "turns"
            await self.game_repo.push_dealer(
                chat_id=chat_id,
                action=action,  # type: ignore
            )
            return

        await message.answer(
            text=f"Ход игрока {next_player.username}",
            reply_markup=game_btns(player_id=next_player.tg_id),
        )
        await self.game_repo.cache_game(game)

    async def bid_timer(
        self,
        message: Message,
    ):
        chat_id = message.chat.id

        game_schema = await self.game_repo.get_game(chat_id)
        if game_schema is None:
            return

        game = Game.from_dto(game_schema)
        count_out = 0
        players = game.players.values()
        for player in players:
            if player.bid == 0 and player.result is None:
                count_out += 1
                player.result = PlayerResult.OUT
                await message.answer(f"Игрок {player.username} шпатель.")

        if count_out == len(players):
            await message.answer("Все игроки были исключены.")
            await self.game_repo.delete_cache_game(chat_id)
            return

        cur_player = game.get_current_turn_player()
        if cur_player.result is not None:
            cur_player = game.next_player()

        msg = await message.answer(
            text=f"Ход игрока {cur_player.username}",
            reply_markup=game_btns(player_id=cur_player.tg_id),
        )
        timer_manager.create_timer(
            "game:turn",
            chat_id,
            self.kick_afk,
            cur_player.tg_id,
            30,
            msg,
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
    ) -> GameResult | None:
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

        if res.type == SuccessType.ALL_PLAYERS_BET:
            timer_manager.cancel_timer(timer_type="game:bid", chat_id=chat_id)

        new_balance = user_model.balance - bid
        update_user = UserPartial(balance=new_balance)
        await self.user_repo.update_user(
            user=user_model,
            data_update=update_user,
            partial=True,
        )
        await self.game_repo.cache_game(game)
        return res

    async def player_turn_hit(
        self,
        chat_id: int,
        user_tg_id: int,
    ) -> GameResult | None:
        timer_manager.cancel_timer(
            timer_type="game:turn",
            chat_id=chat_id,
            player_id=user_tg_id,
        )

        game_schema = await self.game_repo.get_game(chat_id=chat_id)
        if not game_schema:
            logger.debug("Игра в чате с айди chat_id=%s не была найдена", chat_id)
            return None

        game = Game.from_dto(game_schema)
        res = game.player_hit(player_id=user_tg_id)
        if not res.success:
            return res

        await self.game_repo.cache_game(game)
        if res.data.get("dealer_turn") is True:
            action = "reveal" if game.current_round == 2 else "turns"
            await self.game_repo.push_dealer(
                chat_id=chat_id,
                action=action,  # type: ignore
            )

        return res

    async def player_turn_stand(
        self,
        chat_id: int,
        user_tg_id: int,
    ):
        timer_manager.cancel_timer(
            timer_type="game:turn",
            chat_id=chat_id,
            player_id=user_tg_id,
        )
        game_schema = await self.game_repo.get_game(chat_id=chat_id)
        if not game_schema:
            # logger.debug(
            #     "Игра в чате с айди chat_id=%s не была найдена",
            #     chat_id,
            # )
            return None

        game = Game.from_dto(game_schema)
        res = game.player_stand(player_id=user_tg_id)
        if not res.success:
            return res

        await self.game_repo.cache_game(game)

        if res.data.get("dealer_turn") == True:
            if game.round == 1:
                await self.game_repo.push_dealer(chat_id=chat_id, action="reveal")
            elif game.round == 2:
                await self.game_repo.push_dealer(chat_id=chat_id, action="turns")
        return res

    async def dealer_reveal_secret(
        self,
        chat_id: int,
    ):
        game_schema = await self.game_repo.get_game(chat_id=chat_id)
        if not game_schema:
            logger.debug("Игра в чате с айди chat_id=%s не была найдена", chat_id)
            return None

        game = Game.from_dto(game_schema)

        res = game.init_second_round()

        await self.game_repo.cache_game(game)

        return res

    async def dealer_turns(self, chat_id: int):
        game_schema = await self.game_repo.get_game(chat_id=chat_id)
        if not game_schema:
            # logger.debug(
            #     "Игра в чате с айди chat_id=%s не была найдена",
            #     chat_id,
            # )
            return None

        game = Game.from_dto(game_schema)

        res = game.dealer_turns()

        await self.game_repo.cache_game(game)

        return res

    async def ending_game(self, chat_id: int):
        game_schema = await self.game_repo.get_game(chat_id)
        if not game_schema:
            # logger.debug(
            #     "Игра в чате с айди chat_id=%s не была найдена",
            #     chat_id,
            # )
            return None

        game = Game.from_dto(game_schema)
        res = game.result_of_game()
        wins = res.get("wins")
        push = res.get("push")

        players = wins + push
        await update_users_balance(user_repo=self.user_repo, players=players)

        await self.game_repo.delete_cache_game(chat_id)
        return res


# я обязательно доделаю..
