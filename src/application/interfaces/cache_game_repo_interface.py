from abc import ABC, abstractmethod
from typing import Literal

from domain.entities.game import Game
from application.schemas.game import GameSchema


class CacheGameRepoInterface(ABC):
    @abstractmethod
    async def cache_game(self, game: Game) -> GameSchema:
        """Кэшировать игру"""
        pass

    @abstractmethod
    async def get_game(self, chat_id: int) -> GameSchema:
        """Вытащить игру из кэша"""
        pass

    @abstractmethod
    async def delete_cache_game(self, chat_id: int) -> None:
        """Удалить игру из кэша"""
        pass

    @abstractmethod
    async def set_game_state(self, chat_id: int):
        pass

    @abstractmethod
    async def push_dealer(
        self,
        chat_id: int,
        action: Literal["turns", "reveal"],
    ):
        pass

    @abstractmethod
    async def push_ending(self, chat_id: int):
        pass
