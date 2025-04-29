from dataclasses import asdict

from src.infrastructure.repositories import SQLAlchemyUserRepository
from src.domain.entities import User


class UserNotFound(Exception):
    pass


class UserService:
    def __init__(self, user_repo: SQLAlchemyUserRepository):
        self.user_repo = user_repo

    async def get_user_profile(self, user_id: int):
        user_schema = await self.user_repo.get_user_by_tg_id(user_id)
        if user_schema is None:
            raise UserNotFound("Пользователь не был найден")
        user = User.from_dto(user_schema)
        data = asdict(user)
        return data
