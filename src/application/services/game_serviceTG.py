import logging
import asyncio
from typing import Any

from aiogram.types import Message

from src.application.schemas import GameSchema, LobbySchema, UserPartial
from src.infrastructure.repositories import RedisGameCacheRepo, SQLAlchemyUserRepository
from src.domain.entities import Lobby, Game, Player, PlayerResult
from src.domain.types.game import SuccessType, GameResult
from src.infrastructure.telegram.routers.utils import game_btns

logger = logging.getLogger(__name__)


class GameServiceTG:
    timer_tasks: dict[str, dict[str, Any]] = {}

    def __init__(
        self,
        game_repo: RedisGameCacheRepo,
        user_repo: SQLAlchemyUserRepository | None = None,
    ):
        self.game_repo = game_repo
        self.user_repo = user_repo

    @staticmethod
    def _get_turn_timer_key(
        chat_id: int,
        user_id: int,
    ) -> str:
        return str(user_id) + str(chat_id)

    @classmethod
    def save_timer_task(
        cls,
        key: str,
        task: asyncio.Task,
        data: dict[str, Any] = {},
    ):
        data["task"] = task
        cls.timer_tasks[key] = data

    @classmethod
    def cancel_turn_timer(
        cls,
        id: int,
    ):
        try:
            data = cls.timer_tasks.pop(id)
        except KeyError:
            logger.warning("KeyError таймера игрока с айди %s", id)
            return
        task: asyncio.Task = data.get("task")
        task.cancel()
        del data

    async def _turn_timer(
        self,
        message: Message,
    ):
        """
        Таймер времени данного на принятие действия игроку.

        Args:
            message (Message): Сообщение айограм

        Returns:
        """
        chat_id = message.chat.id
        await asyncio.sleep(20)

        game_schema = await self.game_repo.get_game(chat_id)
        if game_schema is None:
            return
        game = Game.from_dto(game_schema)

        player = game.get_current_turn_player()
        player.result = PlayerResult.OUT
        await message.answer(f"Игрок {player.username} шпатель.")

        next_player = game.next_player()
        if next_player is None:
            await message.answer(f"Дилер учится делать ход.")
            return

        msg = await message.answer(
            text=f"Ход игрока {next_player.username}",
            reply_markup=game_btns(player_id=next_player.tg_id),
        )
        task = asyncio.create_task(self._turn_timer(message=msg))
        GameServiceTG.timer_tasks.pop(player.tg_id)
        next_player_turn_key = self._get_turn_timer_key(
            chat_id=msg.chat.id,
            user_id=next_player.tg_id,
        )
        GameServiceTG.save_timer_task(
            id=next_player_turn_key,
            task=task,
        )
        await self.game_repo.cache_game(game)

    def set_turn_timer(
        self,
        message: Message,
        player_id: int,
    ):
        """
        Установить таймер на ход игроку

        Args:
            message (Message): Сообщение айограм
            player_id (int): Айди игрока

        Returns:
        """
        task = asyncio.create_task(self._turn_timer(message=message))
        timer_key = self._get_turn_timer_key(
            chat_id=message.chat.id,
            user_id=player_id,
        )
        GameServiceTG.save_timer_task(
            key=timer_key,
            task=task,
        )

    async def bid_timer(
        self,
        message: Message,
    ):
        """
        Таймер времени данного на ставку

        Args:
            message (Message): Сообщение айограм

        Returns:
        """
        chat_id = message.chat.id
        await asyncio.sleep(25)

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

        GameServiceTG.timer_tasks.pop(str(chat_id))

        if count_out == len(players):
            await message.answer("Все игроки шпатели.")
            await self.game_repo.delete_cache_game(chat_id)
            return

        cur_player = game.get_current_turn_player()
        if not cur_player.result is None:
            cur_player = game.next_player()

        msg = await message.answer(
            text=f"Ход игрока {cur_player.username}",
            reply_markup=game_btns(player_id=cur_player.tg_id),
        )
        task = asyncio.create_task(self._turn_timer(message=msg))
        GameServiceTG.save_timer_task(
            key=self._get_turn_timer_key(
                chat_id=msg.chat.id,
                user_id=cur_player.tg_id,
            ),
            task=task,
        )
        await self.game_repo.set_game_state(chat_id)
        await self.game_repo.cache_game(game)

    async def create_game(
        self,
        lobby_schema: LobbySchema,
    ) -> GameSchema | None:
        """
        Метод создания сущности игры из лобби

        Args:
            lobby_schema (LobbySchema): Пайдентик схема лобби.

        Returns:
            GameSchema: Пайдентик схема игры.
        """
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
    ) -> GameResult:
        """
        Обрабатывает ставку игрока в текущей игровой сессии.

        Args:
            chat_id (int): ID Telegram-чата, где идёт игра.
            user_tg_id (int): Telegram ID игрока.
            bid (int): Сумма ставки, которую поставил игрок.

        Returns:
            GameResult: Обьект результата.
        """
        game_schema = await self.game_repo.get_game(chat_id=chat_id)
        if not game_schema:
            logger.debug("Игра в чате с айди chat_id=%s не была найдена", chat_id)
            return None

        user_model = await self.user_repo.get_user_by_tg_id(
            tg_id=user_tg_id,
            schema=False,
        )
        if bid > user_model.balance:
            logger.debug(
                "Ставка %s превышает баланс %s игрока id=%s",
                bid,
                user_model.balance,
                user_model.id,
            )
            return None

        game = Game.from_dto(game_schema)
        res = game.player_bid(
            player_id=user_tg_id,
            bid=bid,
        )
        if not res.success:
            logger.debug("Ставка не удалась по причине %s", res.type)
            return res

        if res.type == SuccessType.ALL_PLAYERS_BET:
            data = GameServiceTG.timer_tasks.pop(chat_id)
            task: asyncio.Task = data["task"]
            task.cancel()

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
    ) -> GameResult:
        """
        Метод обработки hit действия игрока

        Args:
            chat_id (int): Чат в котором происходит игра
            user_tg_id (int): Телеграм айди игрока

        Returns:
            GameResult: Обьект результата
        """
        GameServiceTG.cancel_turn_timer(id=user_tg_id)

        game_schema = await self.game_repo.get_game(chat_id=chat_id)
        if not game_schema:
            logger.debug("Игра в чате с айди chat_id=%s не была найдена", chat_id)
            return None

        game = Game.from_dto(game_schema)
        res = game.player_hit(player_id=user_tg_id)
        if not res.success:
            return res

        await self.game_repo.cache_game(game)
        if res.data.get("next_player") is None:
            # TODO: ивент воркеру на ход дилера в таком то чате.
            return res

        return res

    async def player_turn_stand(
        self,
        chat_id: int,
        user_tg_id: int,
    ):
        """
        Метод обработки stand действия игрока

        Args:
            chat_id (int): Чат в котором происходит игра
            user_tg_id (int): Телеграм айди игрока

        Returns:
            GameResult: Обьект результата
        """
        GameServiceTG.cancel_turn_timer(id=user_tg_id)

        game_schema = await self.game_repo.get_game(chat_id=chat_id)
        if not game_schema:
            logger.debug("Игра в чате с айди chat_id=%s не была найдена", chat_id)
            return None

        game = Game.from_dto(game_schema)
        res = game.player_stand(player_id=user_tg_id)
        if not res.success:
            return res

        await self.game_repo.cache_game(game)

        if res.data.get("next_player") is None:
            # TODO: ивент воркеру на ход дилера в таком то чате.
            return res

        return res

    async def dealer_hit(self, chat_id: int) -> GameResult:
        pass
