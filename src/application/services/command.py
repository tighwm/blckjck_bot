from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, auto
from typing import Any

from application.interfaces import BaseTelegramUserRepo, LeaderBoardInterface
from application.schemas.user import UserPartial
from domain.types.user.exceptions import (
    UserNotFound,
    BonusCooldownNotExpired,
    BonusOnlyBellowFiveBalance,
)
from domain.entities import User


class ResponseType(Enum):
    BONUS_GAVE = auto()
    TOO_EARLY_FOR_BONUS = auto()
    ONLY_BELLOW_FIVE_BALANCE = auto()


@dataclass
class Response:
    success: bool
    type: ResponseType
    data: dict[str, Any] | None = None


def format_cooldown(delta: timedelta):
    total = delta.total_seconds()
    hours = total // 3600
    minutes = (total % 3600) // 60

    if hours > 0:
        return f"{int(hours)}ч {int(minutes)}м"
    return f"{int(minutes)}м"


class CommandService:
    def __init__(
        self,
        user_repo: BaseTelegramUserRepo,
        board_repo: LeaderBoardInterface,
    ):
        self.user_repo = user_repo
        self.board_repo = board_repo

    async def get_user_profile(self, user_id: int):
        user_schema = await self.user_repo.get_user_by_tg_id(user_id)
        if user_schema is None:
            raise UserNotFound(f"User with {user_id} id not found")
        return user_schema

    async def get_balance_leaderboard(self):
        res = self.board_repo.get_leaderboard(board="balance")

    async def give_bonus(
        self,
        user_id: int,
    ):
        user_schema = await self.user_repo.get_user_by_tg_id(user_id)
        if user_schema is None:
            raise UserNotFound(f"User with {user_id} id not found")
        user = User.from_dto(user_schema)
        try:
            user.get_bonus()
        except BonusCooldownNotExpired as e:
            data = {"cooldown": format_cooldown(e.cooldown)}
            return Response(
                success=False,
                type=ResponseType.TOO_EARLY_FOR_BONUS,
                data=data,
            )
        except BonusOnlyBellowFiveBalance:
            return Response(
                success=False,
                type=ResponseType.ONLY_BELLOW_FIVE_BALANCE,
            )

        user_model = await self.user_repo.get_user_by_tg_id(
            tg_id=user_id,
            schema=False,
        )
        user_update = UserPartial(
            balance=user.balance,
            date_bonus=user.date_bonus,
        )
        await self.user_repo.update_user(
            user=user_model,
            data_update=user_update,
            partial=True,
        )

        return Response(success=True, type=ResponseType.BONUS_GAVE)
