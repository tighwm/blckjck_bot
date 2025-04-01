from datetime import datetime
from pydantic import BaseModel

from src.application.schemas import CardSchema, DealerSchema, PlayerSchema


class GameSchema(BaseModel):
    chat_id: int
    players: dict[int, PlayerSchema]
    turn_order: tuple[int, ...]
    dealer: DealerSchema
    deck: list[CardSchema]
    created_at: datetime
    current_player_index: int = 0
