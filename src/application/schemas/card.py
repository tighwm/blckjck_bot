from pydantic import BaseModel
from src.domain.entities.card import Rank, Suit


class CardSchema(BaseModel):
    rank: Rank
    suit: Suit
