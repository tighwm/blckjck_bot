from application.interfaces import BaseTelegramUserRepo, LeaderBoardInterface


class UserNotFound(Exception):
    pass


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
