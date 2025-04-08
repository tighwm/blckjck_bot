import asyncio

from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from src.application.interfaces import TelegramUserRepoMixin
from src.application.schemas import LobbySchema
from src.infrastructure.repositories import RedisLobbyCacheRepoTG
from src.infrastructure.telegram.routers.states import ChatState
from src.domain.entities import Lobby, User


class LobbyServiceTG:
    timer_tasks: dict[int, dict[str, asyncio.Task | Message]] = {}

    def __init__(
        self,
        lobby_repo: RedisLobbyCacheRepoTG,
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
        return User.from_dto(user_schema)

    @classmethod
    def save_timer(
        cls,
        message: Message,
        task: asyncio.Task,
    ):
        cls.timer_tasks[message.chat.id] = {"task": task, "message": message}

    async def lobby_timer(
        self,
        message: Message,
        state: FSMContext,
        timer_out: int = 15,
    ):
        lobby_schema = None
        while timer_out > 5:
            await asyncio.sleep(5)
            timer_out -= 5
            lobby_schema = await self.lobby_repo.get_lobby(message.chat.id)
            text = (
                f"Возможно набор на игру начался, я ебу что ли\n"
                f"Игроки: {lobby_schema.str_users()}\n"
                f"Таймер: {timer_out}"
            )
            await message.edit_text(text=text)

        chat_id = lobby_schema.chat_id
        async with self.lobby_repo.with_lock(chat_id):
            await self.lobby_repo.push_starting(
                chat_id=chat_id,
                message=message,
            )
            LobbyServiceTG.timer_tasks.pop(chat_id)
            await message.delete()
            await state.set_state(ChatState.bid)
            await self.lobby_repo.delete_lobby(chat_id)

    async def create_lobby(
        self,
        chat_id: int,
        user_id: int,
    ) -> LobbySchema:
        async with self.lobby_repo.with_lock(chat_id):
            lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
            if lobby_schema:
                return None

            user_schema = await self.user_repo.get_user_by_tg_id(tg_id=user_id)
            user = User.from_dto(user_schema)
            lobby = Lobby(chat_id=chat_id, users=[user])
            return await self.lobby_repo.cache_lobby(lobby=lobby)

    async def add_user(
        self,
        chat_id: int,
        user_id: int,
    ) -> LobbySchema:
        async with self.lobby_repo.with_lock(chat_id):
            lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
            if not lobby_schema:
                return None
            if self._check_user_in_lobby(
                user_id=user_id,
                lobby_schema=lobby_schema,
            ):
                return None

            user = await self._get_user_entities(user_id=user_id)
            lobby = Lobby.from_dto(lobby_schema)
            lobby.add_user(user)
            return await self.lobby_repo.cache_lobby(lobby=lobby)

    async def remove_user(
        self,
        chat_id: int,
        user_id: int,
    ) -> LobbySchema:
        async with self.lobby_repo.with_lock(chat_id):
            lobby_schema = await self.lobby_repo.get_lobby(chat_id=chat_id)
            if not lobby_schema:
                return None
            if not self._check_user_in_lobby(
                user_id=user_id,
                lobby_schema=lobby_schema,
            ):
                return None

            user = await self._get_user_entities(user_id=user_id)
            lobby = Lobby.from_dto(lobby_schema)
            lobby.delete_user(user)
            return await self.lobby_repo.cache_lobby(lobby=lobby)

    async def cancel_lobby(
        self,
        chat_id: int,
    ):
        res = await self.lobby_repo.exists_lobby(chat_id)
        if not res:
            return False

        await self.lobby_repo.delete_lobby(chat_id=chat_id)
        timer_task = LobbyServiceTG.timer_tasks.pop(chat_id)
        if timer_task:
            timer_task["task"].cancel()
            await timer_task["message"].delete()
        return True
