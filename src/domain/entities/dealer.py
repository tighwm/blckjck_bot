from dataclasses import dataclass, field

from src.domain.entities.card import Card


@dataclass
class Dealer:
    cards: list[Card] = field(default_factory=list)

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
