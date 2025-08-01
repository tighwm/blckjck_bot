from abc import ABC, abstractmethod

from domain.entities import Lobby
from application.schemas import LobbySchema


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
    ) -> LobbySchema | None:
        """Получить лобби из кэша"""
        pass

    @abstractmethod
    async def delete_lobby(
        self,
        chat_id: int,
    ) -> None:
        """Удалить лобби из кэша"""
        pass

    @abstractmethod
    async def exists_lobby(
        self,
        chat_id: int,
    ):
        """Проверить существование лобби"""
        pass

    @abstractmethod
    def with_lock(
        self,
        chat_id: int,
    ):
        pass


class BaseCacheLobbyRepoTG(CacheLobbyRepoInterface):
    @abstractmethod
    async def push_starting(self, chat_id: int):
        pass
