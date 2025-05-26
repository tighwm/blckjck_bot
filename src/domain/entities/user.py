from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

from domain.types.user.exceptions import (
    BonusCooldownNotExpired,
    BonusOnlyBellowFiveBalance,
)

if TYPE_CHECKING:
    from src.application.schemas import UserSchema


BONUS_DELTA = timedelta(days=1)


@dataclass
class User:
    id: int
    tg_id: int
    first_name: str
    username: str | None
    balance: int
    registered_at: datetime
    date_bonus: datetime | None

    @classmethod
    def from_dto(cls, data: "UserSchema") -> "User":
        return cls(
            id=data.id,
            tg_id=data.tg_id,
            first_name=data.first_name,
            username=data.username,
            balance=data.balance,
            registered_at=data.registered_at,
            date_bonus=data.date_bonus,
        )

    def get_bonus(self):
        if self.balance > 5:
            raise BonusOnlyBellowFiveBalance()

        now = datetime.now(timezone.utc)
        delta = now - self.date_bonus
        if delta >= BONUS_DELTA:
            self.balance += 125
            self.date_bonus = now
        else:
            raise BonusCooldownNotExpired(
                message="Too early for bonus.",
                cooldown=BONUS_DELTA - delta,
            )
