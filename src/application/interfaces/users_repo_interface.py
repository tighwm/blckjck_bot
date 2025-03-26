from abc import ABC, abstractmethod
from src.application.schemas.user import UserCreate, UserUpdate, UserPartial, UserSchema


class UserRepoInterface(ABC):
    @abstractmethod
    async def create_user(self, user: UserCreate):
        """Создание пользователя"""
        pass

    @abstractmethod
    async def get_user_by_id(self, id: int):
        """Получить юзера по айди"""
        pass

    @abstractmethod
    async def update_user(self, data_update: UserPartial | UserUpdate):
        """Обновить полностью либо частично"""
        pass

    @abstractmethod
    async def delete_user(self, user: UserSchema):
        """Удалить пользователя"""
        pass


class TelegramUserRepoMixin(ABC):
    @abstractmethod
    async def get_user_by_tg_id(self, tg_id: int):
        pass
