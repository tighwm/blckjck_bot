from pydantic import BaseModel, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    tg_id: int
    username: str | None = None
    date_bonus: datetime


class UserCreate(UserBase):
    date_bonus: datetime | None = None


class UserUpdate(UserCreate):
    pass


class UserPartial(UserUpdate):
    tg_id: None = None
    balance: int | None = None


class UserSchema(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    balance: int
    registered_at: datetime
