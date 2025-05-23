from aiogram import Router

from .commands import router as com_router
from .game_handlers import router as game_router
from .lobby_handlers import router as lob_router

__all__ = "router"

router = Router()
router.include_routers(
    com_router,
    game_router,
    lob_router,
)
