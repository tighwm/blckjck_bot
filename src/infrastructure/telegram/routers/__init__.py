from aiogram import Router
from src.infrastructure.telegram.routers.chat_handlers import router as chat_router
from src.infrastructure.telegram.routers.callback_handlers import (
    router as callback_router,
)

__all__ = ("routers",)

routers = Router()
routers.include_routers(
    chat_router,
    callback_router,
)
