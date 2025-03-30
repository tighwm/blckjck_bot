from abc import ABC, abstractmethod

from src.domain.entities.game import Game
from src.application.schemas.game import GameSchema


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
