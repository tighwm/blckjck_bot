from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.interfaces.users_repo_interface import (
    BaseTelegramUserRepo,
)
from application.schemas.user import UserSchema, UserPartial, UserUpdate, UserCreate
from infrastructure.database import User as UserModel


class SQLAlchemyUserRepositoryTG(BaseTelegramUserRepo):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self,
        user_in: UserCreate,
    ) -> UserSchema:
        user_model = UserModel(**user_in.model_dump())
        self.session.add(user_model)
        await self.session.commit()
        return UserSchema.model_validate(user_model)

    async def get_user_by_id(
        self,
        user_id: int,
        schema: bool = True,
    ) -> UserSchema | UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)  # type: ignore
        user_model = await self.session.scalar(stmt)
        if not user_model:
            return None
        if schema:
            return UserSchema.model_validate(user_model)
        return user_model

    async def update_user(
        self,
        user: UserModel,
        data_update: UserUpdate | UserPartial,
        partial: bool = False,
    ) -> UserSchema:
        user_update = data_update.model_dump(exclude_unset=partial).items()
        for name, value in user_update:
            setattr(user, name, value)
        await self.session.commit()
        return UserSchema.model_validate(user)

    async def get_user_by_tg_id(
        self,
        tg_id: int,
        schema: bool = True,
    ) -> UserSchema | UserModel | None:
        stmt = select(UserModel).where(UserModel.tg_id == tg_id)  # type: ignore
        user_model = await self.session.scalar(stmt)
        if not user_model:
            return None
        if schema:
            return UserSchema.model_validate(user_model)
        return user_model

    async def get_users_by_tg_ids(
        self,
        tg_ids: list[int],
        schema: bool = True,
    ):
        stmt = select(UserModel).where(UserModel.tg_id.in_(tg_ids))
        users_models = await self.session.scalars(stmt)
        return users_models.all()

    async def update_users(
        self,
        datas_update: dict[UserModel, UserUpdate | UserPartial],
        partial: bool = False,
    ):
        schemas = []

        for model, data_update in datas_update.items():
            update_data = data_update.model_dump(exclude_unset=partial)
            for name, value in update_data.items():
                setattr(model, name, value)
            schemas.append(UserSchema.model_validate(model))

        await self.session.commit()
        return schemas

    async def delete_user(
        self,
        user: UserModel,
    ) -> None:
        await self.session.delete(user)
        return None
