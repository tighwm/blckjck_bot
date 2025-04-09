from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.domain.entities import Card

if TYPE_CHECKING:
    from src.application.schemas import DealerSchema


@dataclass
class Dealer:
    cards: list[Card] = field(default_factory=list)

    def _calculate_score(self) -> int:
        if not self.cards:
            return 0

        score = sum(card.get_value() for card in self.cards)

        aces_count = sum(1 for card in self.cards if card.rank == "A")
        while score > 21 and aces_count > 0:
            score -= 10
            aces_count -= 1

        return score

    @property
    def score(self):
        return self._calculate_score()

    def has_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.score == 21

    def is_busted(self) -> bool:
        return self.score > 21

    def cards_str(self) -> str:
        if not self.cards:
            return "Нет карт"
        return ", ".join(map(str, self.cards))

    @classmethod
    def from_dto(cls, data: "DealerSchema") -> "Dealer":
        return cls(
            cards=[Card.from_dto(card_schema) for card_schema in data.cards],
        )
