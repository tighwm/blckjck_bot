from enum import Enum
from typing import TYPE_CHECKING
from dataclasses import dataclass, field

from src.domain.entities import Card

if TYPE_CHECKING:
    from src.application.schemas import PlayerSchema


class PlayerResult(Enum):
    WIN = "win"
    LOSE = "lose"
    OUT = "out"


@dataclass
class Player:
    username: str | None
    tg_id: int
    bid: int = 0
    cards: list[Card] = field(default_factory=list)
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

    @classmethod
    def from_dto(cls, data: "PlayerSchema") -> "Player":
        return cls(
            username=data.username,
            tg_id=data.tg_id,
            bid=data.bid,
            cards=[Card.from_dto(card_schema) for card_schema in data.cards],
            result=data.result,
        )
