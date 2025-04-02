import random
from datetime import datetime
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.domain.entities import Card, Rank, Suit, Player, Dealer
from src.domain.types.game import GameResult, ErrorType, ErrorMessages, SuccessType

if TYPE_CHECKING:
    from src.application.schemas import GameSchema


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

    @classmethod
    def from_dto(cls, data: "GameSchema") -> "Game":
        return cls(
            chat_id=data.chat_id,
            players={
                user_tg_id: Player.from_dto(player_schema)
                for user_tg_id, player_schema in data.players.items()
            },
            dealer=Dealer.from_dto(data.dealer),
            deck=[Card.from_dto(card_schema) for card_schema in data.deck],
            created_at=data.created_at,
            current_player_index=data.current_player_index,
            turn_order=data.turn_order,
        )

    def _get_current_turn_player(self):
        return self.players.get(self.turn_order[self.current_player_index])

    def _get_player(
        self,
        player_id: int,
    ):
        return self.players.get(player_id)

    def _check_all_bets(self) -> bool:
        return any(player.bid != 0 for player in self.players.values())

    def player_bid(
        self,
        player_id: int,
        bid: int,
    ) -> GameResult:
        player = self._get_player(player_id)
        if not player:
            return GameResult(
                success=False,
                type=ErrorType.PLAYER_NOT_FOUND,
                message=ErrorMessages.get(
                    ErrorType.PLAYER_NOT_FOUND,
                    player_id=player_id,
                ),
            )

        player.bid = bid
        if self._check_all_bets():
            return GameResult(
                success=True,
                type=SuccessType.ALL_PLAYERS_BET,
                data={"player": self._get_current_turn_player()},
            )

        return GameResult(
            success=True,
            type=SuccessType.BID_ACCEPTED,
        )
