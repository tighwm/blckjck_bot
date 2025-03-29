__all__ = (
    "CacheGameRepoInterface",
    "CacheLobbyRepoInterface",
    "UserRepoInterface",
    "TelegramUserRepoMixin",
)

from src.application.interfaces.cache_game_repo_interface import CacheGameRepoInterface
from src.application.interfaces.cache_lobby_repo_interface import (
    CacheLobbyRepoInterface,
)
from src.application.interfaces.users_repo_interface import (
    UserRepoInterface,
    TelegramUserRepoMixin,
)
