from enum import Enum
from pydantic import BaseModel, Field

from src.domain.entities.card import Card


class PlayerResult(Enum):
    WIN = "win"
    LOSE = "lose"
    OUT = "out"


class Player(BaseModel):
    username: str | None
    user_tg_id: int
    bid: int = 0
    cards: list[Card] = Field(default_factory=list)
    result: PlayerResult | None = None

    def calculate_score(self) -> int:
        score = sum(card.get_value() for card in self.cards)

        aces_count = sum(1 for card in self.cards if card.rank == "A")
        while score > 21 and aces_count > 0:
            score -= 10
            aces_count -= 1

        return score

    @property
    def score(self):
        return self.calculate_score()

    def has_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.score == 21

    def is_busted(self) -> bool:
        return self.score > 21
