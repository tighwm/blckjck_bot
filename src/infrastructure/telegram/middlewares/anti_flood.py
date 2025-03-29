import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message, CallbackQuery


class AntiFlood(BaseMiddleware):
    def __init__(self):
        self.users_data: dict[int, dict[str, Any]] = {}
        self.rate: float = 1.0

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        rate = get_flag(data, "rate_limit")
        if not rate:
            rate = self.rate

        user_id = event.from_user.id
        now = time.time()
        template = {
            "last_time": now,
            "flood_count": 0,
            "block": False,
        }

        if user_id not in self.users_data:
            self.users_data[user_id] = template
            return await handler(event, data)

        user_data = self.users_data.get(user_id)
        delta = now - user_data.get("last_time")

        if user_data.get("block"):
            if delta > 10:
                self.users_data[user_id] = template
                return await handler(event, data)
            return

        if delta > rate:
            self.users_data[user_id] = template
            return await handler(event, data)

        user_data["last_time"] = now
        user_data["flood_count"] += 1
        if user_data.get("flood_count") >= 3:
            user_data["block"] = True
        self.users_data[user_id] = user_data
        return
