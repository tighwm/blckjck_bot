from datetime import datetime, timezone

from sqlalchemy import func, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database import Base


class User(Base):

    @staticmethod
    def get_utc_now():
        return datetime.now(tz=timezone.utc)

    username: Mapped[str | None] = mapped_column(nullable=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=get_utc_now,
    )
    balance: Mapped[int] = mapped_column(
        nullable=False,
        default=100,
        server_default="100",
    )

    def __repr__(self):
        return (
            f"User username={self.username}, tg_id={self.tg_id}, balance={self.balance}"
        )
