from pydantic import BaseModel

from application.schemas import UserSchema


class LobbySchema(BaseModel):
    chat_id: int
    users: list[UserSchema]

    @property
    def names(self):
        return ", ".join([user.first_name for user in self.users])
