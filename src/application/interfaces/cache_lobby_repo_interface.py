from abc import ABC, abstractmethod

from src.domain.entities.lobby import Lobby


class CacheLobbyRepoInterface(ABC):
    @abstractmethod
    async def create_lobby(
        self,
        lobby: Lobby,
    ):
        """Сохранить лобби в кэш"""
        pass

    @abstractmethod
    async def get_lobby(
        self,
        chat_id: int,
    ):
        """Получить лобби из кэша"""
        pass

    @abstractmethod
    async def delete_lobby(
        self,
        chat_id: int,
    ):
        """Удалить лобби из кэша"""
        pass
