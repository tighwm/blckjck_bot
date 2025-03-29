from abc import ABC, abstractmethod

from src.domain.entities import Lobby
from src.application.schemas import LobbySchema


class CacheLobbyRepoInterface(ABC):
    @abstractmethod
    async def cache_lobby(
        self,
        lobby: Lobby,
    ) -> LobbySchema:
        """Сохранить лобби в кэш"""
        pass

    @abstractmethod
    async def get_lobby(
        self,
        chat_id: int,
    ) -> LobbySchema:
        """Получить лобби из кэша"""
        pass

    @abstractmethod
    async def delete_lobby(
        self,
        chat_id: int,
    ) -> None:
        """Удалить лобби из кэша"""
        pass
