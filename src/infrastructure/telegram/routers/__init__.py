from aiogram import Router
from src.infrastructure.telegram.routers.chat_handlers import router as chat_router

__all__ = ("routers",)

routers = Router()
routers.include_routers(
    chat_router,
)
