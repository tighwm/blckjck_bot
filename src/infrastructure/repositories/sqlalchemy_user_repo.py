from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.users_repo_interface import (
    TelegramUserRepoMixin,
)
from src.application.schemas.user import UserSchema, UserPartial, UserUpdate, UserCreate
from src.infrastructure.database import User


class SQLAlchemyUserRepository(TelegramUserRepoMixin):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self,
        user_in: UserCreate,
    ) -> UserSchema:
        user_model = User(**user_in.model_dump())
        self.session.add(user_model)
        await self.session.commit()
        return UserSchema.model_validate(user_model)

    async def get_user_by_id(
        self,
        id: int,
    ) -> UserSchema | None:
        stmt = select(User).where(User.id == id)
        user_model = await self.session.scalar(stmt)
        if not user_model:
            return None
        return UserSchema.model_validate(user_model)

    async def update_user(
        self,
        user: User,
        data_update: UserUpdate | UserPartial,
        partitial: bool = False,
    ) -> UserSchema:
        user_update = data_update.model_dump(exclude_unset=partitial).items()
        for name, value in user_update:
            setattr(user, name, value)
        await self.session.commit()
        return UserSchema.model_validate(user)

    async def get_user_by_tg_id(
        self,
        tg_id: int,
    ) -> UserSchema | None:
        stmt = select(User).where(User.tg_id == tg_id)
        user_model = await self.session.scalar(stmt)
        if not user_model:
            return None
        return UserSchema.model_validate(user_model)

    async def delete_user(
        self,
        user: User,
    ) -> None:
        await self.session.delete(user)
        return None
