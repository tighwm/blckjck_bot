from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.entities import User

if TYPE_CHECKING:
    from src.application.schemas import LobbySchema


@dataclass
class Lobby:
    chat_id: int
    users: list[User]

    def add_user(self, user: User):
        self.users.append(user)

    def delete_user(self, user: User):
        self.users.remove(user)

    @classmethod
    def from_dto(cls, data: "LobbySchema") -> "Lobby":
        return cls(
            chat_id=data.chat_id,
            users=[User.from_dto(user_schema) for user_schema in data.users],
        )
