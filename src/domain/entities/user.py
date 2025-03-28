from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    tg_id: int
    username: str | None
    balance: int
    registered_at: datetime
