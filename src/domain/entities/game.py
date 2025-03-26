import random
from datetime import datetime
from pydantic import BaseModel, Field

from src.domain.entities.card import Card, Rank, Suit
from src.domain.entities.player import Player
from src.domain.entities.dealer import Dealer


def init_deck():
    deck = [Card(rank, suit) for suit in Suit for rank in Rank]

    random.shuffle(deck)
    return deck


class Game(BaseModel):
    chat_id: int
    players: dict[int, Player]
    turn_order: tuple[int, ...]
    dealer: Dealer = Field(default_factory=Dealer)
    deck: list[Card] = Field(default_factory=init_deck)
    created_at: datetime = Field(default_factory=datetime.now)
    current_player_index: int = 0
