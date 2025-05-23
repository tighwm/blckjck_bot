from aiogram import Router
from infrastructure.telegram.routers.chat import router as chat_routers
from infrastructure.telegram.routers.callback_handlers import (
    router as callback_router,
)

__all__ = ("routers",)

routers = Router()
routers.include_routers(
    chat_routers,
    callback_router,
)
