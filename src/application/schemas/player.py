from pydantic import BaseModel

from application.schemas import CardSchema
from domain.entities import PlayerResult


class PlayerSchema(BaseModel):
    name: str | None
    tg_id: int
    bid: int = 0
    cards: list[CardSchema]
    result: PlayerResult | None = None
