from pydantic import BaseModel

from src.application.schemas.card import CardSchema


class DealerSchema(BaseModel):
    cards: list[CardSchema]
