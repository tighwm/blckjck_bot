from typing import Protocol
from abc import ABC, abstractmethod
from datetime import datetime

from application.schemas.user import UserCreate, UserUpdate, UserPartial, UserSchema


class UserModel(Protocol):
    id: int
    tg_id: int
    username: str | None
    balance: int
    registered_at: datetime


class UserRepoInterface(ABC):
    @abstractmethod
    async def create_user(
        self,
        user_in: UserCreate,
    ) -> UserSchema:
        """Создание пользователя"""
        pass

    @abstractmethod
    async def get_user_by_id(
        self,
        id: int,
    ) -> UserSchema | None:
        """Получить юзера по айди"""
        pass

    @abstractmethod
    async def update_user(
        self,
        user: UserModel,
        data_update: UserPartial | UserUpdate,
        partial: bool = False,
    ) -> UserSchema:
        """Обновить полностью либо частично"""
        pass

    @abstractmethod
    async def update_users(
        self,
        datas_update: dict[UserModel, UserUpdate | UserPartial],
        partial: bool = False,
    ):
        pass

    @abstractmethod
    async def delete_user(
        self,
        user: UserSchema,
    ) -> None:
        """Удалить пользователя"""
        pass


class BaseTelegramUserRepo(UserRepoInterface):
    @abstractmethod
    async def get_user_by_tg_id(
        self,
        tg_id: int,
        schema: bool = True,
    ) -> UserSchema | None:
        pass

    @abstractmethod
    async def get_users_by_tg_ids(
        self,
        tg_ids: list[int],
        schema: bool = True,
    ):
        pass
