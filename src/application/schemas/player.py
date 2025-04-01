from pydantic import BaseModel

from src.application.schemas import CardSchema
from src.domain.entities import PlayerResult


class PlayerSchema(BaseModel):
    username: str | None
    tg_id: int
    bid: int = 0
    cards: list[CardSchema]
    result: PlayerResult | None = None
