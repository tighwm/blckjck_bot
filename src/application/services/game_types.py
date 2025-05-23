from dataclasses import dataclass
from enum import Enum, auto


class ResponseType(Enum):
    BID_ACCEPTED = auto()
    BID_DENIED = auto()
    HIT_ACCEPTED = auto()
    STAND_ACCEPTED = auto()

    PLAYER_NOT_FOUND = auto()
    ANOTHER_PLAYER_TURN = auto()


@dataclass
class Response:
    success: bool
    type: ResponseType
    data: dict | None = None
