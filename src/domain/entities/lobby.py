from dataclasses import dataclass

from src.domain.entities.user import User


@dataclass
class Lobby:
    chat_id: int
    users: list[User]

    def add_user(self, user: User):
        self.users.append(user)

    def delete_user(self, user: User):
        self.users.remove(user)
