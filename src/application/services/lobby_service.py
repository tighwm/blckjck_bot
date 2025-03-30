from src.application.interfaces import CacheLobbyRepoInterface, TelegramUserRepoMixin
from src.domain.entities import Lobby, User
from src.infrastructure.database.models.user import User as UserModel
from src.application.schemas import LobbySchema


class LobbyService:
    def __init__(
        self,
        lobby_repo: CacheLobbyRepoInterface,
        user_repo: TelegramUserRepoMixin,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo

    def _check_user_in_lobby(
        self,
        user_id: int,
        lobby_schema: LobbySchema,
    ):
        for user in lobby_schema.users:
            if user.tg_id == user_id:
                return True
        return False

    async def _get_user_entities(
        self,
        user_id: int,
    ) -> User:
        user_schema = await self.user_repo.get_user_by_tg_id(tg_id=user_id)
        return User(**user_schema.model_dump())

    async def create_lobby(
        self,
        chat_id: int,
        user_id: int,
    ) -> LobbySchema:
        lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
        if lobby_schema:
            return None

        user_schema = await self.user_repo.get_user_by_tg_id(tg_id=user_id)
        user = User(**user_schema.model_dump())
        lobby = Lobby(chat_id=chat_id, users=[user])
        return await self.lobby_repo.cache_lobby(lobby=lobby)

    async def add_user(
        self,
        chat_id: int,
        user_id: int,
    ) -> LobbySchema:
        lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
        if not lobby_schema:
            return None
        if self._check_user_in_lobby(
            user_id=user_id,
            lobby_schema=lobby_schema,
        ):
            return None

        user = await self._get_user_entities(user_id=user_id)
        lobby = Lobby(**lobby_schema.model_dump())
        lobby.add_user(user)
        return await self.lobby_repo.cache_lobby(lobby=lobby)

    async def remove_user(self, chat_id: int, user_id: int) -> LobbySchema:
        lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
        if not lobby_schema:
            return None
        if not self._check_user_in_lobby(
            user_id=user_id,
            lobby_schema=lobby_schema,
        ):
            return None

        user = await self._get_user_entities(user_id=user_id)
        lobby = Lobby(**lobby_schema.model_dump())
        lobby.delete_user(user)
        return await self.lobby_repo.cache_lobby(lobby=lobby)
