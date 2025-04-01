from pydantic import BaseModel

from src.application.schemas import CardSchema


class DealerSchema(BaseModel):
    cards: list[CardSchema]
