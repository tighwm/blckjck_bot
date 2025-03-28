from pydantic import BaseModel

from src.application.schemas.user import UserSchema


class LobbySchema(BaseModel):
    chat_id: int
    users: list[UserSchema]
