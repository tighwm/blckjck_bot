from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.schemas import CardSchema


class Rank(str, Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


class Suit(str, Enum):
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"
    SPADES = "spades"


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def get_value(self) -> int:
        if self.rank in {Rank.JACK, Rank.QUEEN, Rank.KING}:
            return 10
        elif self.rank == Rank.ACE:
            return 11
        else:
            return int(self.rank)

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value[0]}"

    @classmethod
    def from_dto(cls, data: "CardSchema") -> "Card":
        return cls(
            rank=data.rank,
            suit=data.suit,
        )
