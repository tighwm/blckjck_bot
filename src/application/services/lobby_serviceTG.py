from aiogram.types import Message

from application.interfaces import BaseTelegramUserRepo
from application.interfaces.cache_lobby_repo_interface import BaseCacheLobbyRepoTG
from application.schemas import LobbySchema
from application.services.timer_mng import timer_manager
from domain.entities import Lobby, User


class LobbyServiceTG:
    def __init__(
        self,
        lobby_repo: BaseCacheLobbyRepoTG,
        user_repo: BaseTelegramUserRepo,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo

    @staticmethod
    def _check_user_in_lobby(
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
        first_name: str,
    ) -> User:
        user_schema = await self.user_repo.get_user_by_tg_id(tg_id=user_id)
        user_schema.first_name = first_name
        return User.from_dto(user_schema)

    async def _lobby_timer(self, chat_id: int):
        async with self.lobby_repo.with_lock(chat_id):
            await self.lobby_repo.push_starting(chat_id=chat_id)
            await self.lobby_repo.delete_lobby(chat_id)

    async def lobby_interval_timer(
        self,
        message: Message,
        remaining_time: int,
    ):
        if remaining_time == 0:
            await message.delete()
        chat_id = message.chat.id
        lobby_schema = await self.lobby_repo.get_lobby(chat_id)
        if lobby_schema is None:
            raise ValueError("Lobby schema can't be None")
        text = (
            f"Запущено лобби на игру.\n"
            f"Игроки: {lobby_schema.names}\n"
            f"Таймер: {remaining_time}"
        )
        await message.edit_text(text)

    async def create_lobby(
        self,
        chat_id: int,
        user_id: int,
        first_name: str,
        timeout: int,
    ) -> LobbySchema | None:
        async with self.lobby_repo.with_lock(chat_id):
            lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
            if lobby_schema:
                return None

            user_schema = await self.user_repo.get_user_by_tg_id(tg_id=user_id)
            user_schema.first_name = first_name
            user = User.from_dto(user_schema)
            lobby = Lobby(chat_id=chat_id, users=[user])
            timer_manager.create_timer(
                "lobby",
                chat_id,
                self._lobby_timer,
                None,
                timeout,
                chat_id,
            )
            return await self.lobby_repo.cache_lobby(lobby=lobby)

    async def add_user(
        self,
        chat_id: int,
        user_id: int,
        first_name: str,
    ) -> LobbySchema | None:
        async with self.lobby_repo.with_lock(chat_id):
            lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
            if not lobby_schema:
                return None
            if self._check_user_in_lobby(
                user_id=user_id,
                lobby_schema=lobby_schema,
            ):
                return None

            user = await self._get_user_entities(
                user_id=user_id,
                first_name=first_name,
            )
            lobby = Lobby.from_dto(lobby_schema)
            lobby.add_user(user)
            return await self.lobby_repo.cache_lobby(lobby=lobby)

    async def remove_user(
        self,
        chat_id: int,
        user_id: int,
    ) -> LobbySchema | None:
        async with self.lobby_repo.with_lock(chat_id):
            lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
            if not lobby_schema:
                return None
            if not self._check_user_in_lobby(
                user_id=user_id,
                lobby_schema=lobby_schema,
            ):
                return None

            lobby = Lobby.from_dto(lobby_schema)
            lobby.delete_user(user_id)
            return await self.lobby_repo.cache_lobby(lobby=lobby)

    async def cancel_lobby(
        self,
        chat_id: int,
    ):
        res = await self.lobby_repo.exists_lobby(chat_id)
        if not res:
            return False

        timer_manager.cancel_timer(
            "lobby",
            chat_id,
            None,
        )
        await self.lobby_repo.delete_lobby(chat_id=chat_id)
        return True
