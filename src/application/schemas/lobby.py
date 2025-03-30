from pydantic import BaseModel

from src.application.schemas.user import UserSchema


class LobbySchema(BaseModel):
    chat_id: int
    users: list[UserSchema]

    def str_users(self) -> str:
        """Строковое представление юзеров в лобби"""
        users_name = [user.username for user in self.users]
        return ", ".join(users_name)
