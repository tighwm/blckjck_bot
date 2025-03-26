from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    tg_id: int
    created_at: datetime
    username: str | None = None
