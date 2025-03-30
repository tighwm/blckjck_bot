import random
from datetime import datetime
from dataclasses import dataclass, field

from src.domain.entities.card import Card, Rank, Suit
from src.domain.entities.player import Player
from src.domain.entities.dealer import Dealer


def deck_factory():
    deck = [Card(rank, suit) for suit in Suit for rank in Rank]

    random.shuffle(deck)
    return deck


def turn_order_factory():
    pass


@dataclass
class Game:
    chat_id: int
    players: dict[int, Player]
    dealer: Dealer = field(default_factory=Dealer)
    deck: list[Card] = field(default_factory=deck_factory)
    created_at: datetime = field(default_factory=datetime.now)
    current_player_index: int = 0
    turn_order: tuple[int, ...] = field(init=False)

    def __post_init__(self):
        self.turn_order = tuple(self.players.keys())
