from dataclasses import dataclass
from typing import TYPE_CHECKING

from domain.entities import User

if TYPE_CHECKING:
    from src.application.schemas import LobbySchema


@dataclass
class Lobby:
    chat_id: int
    users: list[User]

    def add_user(
        self,
        user: User,
    ):
        self.users.append(user)

    def delete_user(
        self,
        user_tg_id: int,
    ):
        for user in self.users:
            if user.tg_id == user_tg_id:
                self.users.remove(user)
                break

    @classmethod
    def from_dto(cls, data: "LobbySchema") -> "Lobby":
        return cls(
            chat_id=data.chat_id,
            users=[User.from_dto(user) for user in data.users],
        )
