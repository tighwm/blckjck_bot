from pydantic import BaseModel

from domain.entities import Rank, Suit


class CardSchema(BaseModel):
    rank: Rank
    suit: Suit
