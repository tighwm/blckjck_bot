from pydantic import BaseModel

from application.schemas import CardSchema


class DealerSchema(BaseModel):
    cards: list[CardSchema]
    first_card: CardSchema | None = None
    secret_card: CardSchema | None = None
