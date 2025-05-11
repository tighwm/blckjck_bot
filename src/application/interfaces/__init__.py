__all__ = (
    "CacheGameRepoInterface",
    "CacheLobbyRepoInterface",
    "UserRepoInterface",
    "BaseTelegramUserRepo",
)

from application.interfaces.cache_game_repo_interface import CacheGameRepoInterface
from application.interfaces.cache_lobby_repo_interface import (
    CacheLobbyRepoInterface,
)
from application.interfaces.users_repo_interface import (
    UserRepoInterface,
    BaseTelegramUserRepo,
)
