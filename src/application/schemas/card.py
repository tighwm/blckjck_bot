from pydantic import BaseModel
from src.domain.entities import Rank, Suit


class CardSchema(BaseModel):
    rank: Rank
    suit: Suit
