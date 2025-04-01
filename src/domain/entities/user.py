from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.schemas import UserSchema


@dataclass
class User:
    id: int
    tg_id: int
    username: str | None
    balance: int
    registered_at: datetime

    @classmethod
    def from_dto(cls, data: "UserSchema") -> "User":
        return cls(
            id=data.id,
            tg_id=data.tg_id,
            username=data.username,
            balance=data.balance,
            registered_at=data.registered_at,
        )
