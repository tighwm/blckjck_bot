from abc import ABC, abstractmethod


class LeaderBoardInterface(ABC):
    @abstractmethod
    async def get_leaderboard(
        self,
        board: str,
        zrange: tuple[int, int] = (0, 9),
    ):
        pass

    @abstractmethod
    async def cache_leaderboard(
        self,
        board: str,
        members: dict[str, int] = None,
    ):
        pass
