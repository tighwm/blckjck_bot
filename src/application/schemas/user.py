from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    tg_id: int
    username: str | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(UserCreate):
    pass


class UserPartial(UserUpdate):
    tg_id: None = None
    balance: int | None = None


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    balance: int
    registered_at: datetime
