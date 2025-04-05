from enum import Enum
from dataclasses import dataclass
from typing import Any


class ErrorType(Enum):
    PLAYER_NOT_FOUND = "player_not_found"


class SuccessType(Enum):
    ALL_PLAYERS_BET = "all_players_bet"
    BID_ACCEPTED = "bid_accepted"

    HIT_ACCEPTED = "hit_accepted"
    HIT_BUSTED = "hit_busted"
    HIT_BLACKJACK = "hit_blackjack"


@dataclass
class GameResult:
    success: bool
    type: SuccessType | ErrorType | None = None
    message: str = ""
    data: dict[str, dict[str, Any]] | None = None


class ErrorMessages:
    @staticmethod
    def get(error_type: ErrorType, **context) -> str:
        messages = {
            ErrorType.PLAYER_NOT_FOUND: "Игрок с ID {player_id} не найден.",
        }
        return messages[error_type].format(**context)
