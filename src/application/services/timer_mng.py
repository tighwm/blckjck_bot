import asyncio
import logging
from functools import partial
from typing import Callable, Any, Awaitable

logger = logging.getLogger(__name__)


class EventTimer:
    def __init__(
        self,
        id_: str,
        timeout: int,
        event: Callable[..., Awaitable[Any]],
        *args,
        **kwargs,
    ):
        self.id = id_
        self.timeout = timeout
        self.event = partial(event, *args, **kwargs)

        self._task: asyncio.Task | None = None

    async def _timer_start(self):
        await asyncio.sleep(self.timeout)
        try:
            await self.event()
        except Exception as e:
            import traceback

            logger.error(
                "EventTimer error id=%s: %s\nTraceback:%s",
                self.id,
                e,
                traceback.format_exc(),
            )

    def start(self):
        self._task = asyncio.create_task(self._timer_start())

    def cancel(self):
        if self._task is None:
            logger.warning("Timer id=%s not found.", self.id)
            return
        self._task.cancel()

    def __str__(self):
        return f"Timer id={self.id}, timeout={self.timeout}"


class IntervalEventTimer(EventTimer):
    def __init__(
        self,
        id_: str,
        timeout: int,
        interval: int,
        event: Callable[..., Awaitable[Any]],
        *args,
        **kwargs,
    ):
        super().__init__(id_, timeout, event, *args, **kwargs)
        self.interval = interval

    async def _timer_start(self):
        remaining_time = self.timeout

        err_count = 0
        while remaining_time > self.interval:
            await asyncio.sleep(self.interval)
            remaining_time -= self.interval

            try:
                await self.event(remaining_time=remaining_time)
            except Exception as e:
                import traceback

                err_count += 1
                logger.error(
                    "IntervalTimer error while executing event id=%s: %s\nTraceback:%s",
                    self.id,
                    e,
                    traceback.format_exc(),
                )
                if err_count == 2:
                    break


class TimersManager:
    def __init__(self):
        self._timers: dict[str, EventTimer] = {}

    @staticmethod
    def _get_timer_key(
        timer_type: str,
        chat_id: int,
        player_id: int = None,
    ) -> str:
        if player_id is not None:
            return f"{timer_type}:{chat_id}:{player_id}"
        return f"{timer_type}:{chat_id}"

    def create_timer(
        self,
        timer_type: str,
        chat_id: int,
        event: Callable[..., Awaitable[Any]],
        player_id: int | None = None,
        timeout: int = 30,
        *args,
        **kwargs,
    ):
        timer_key = self._get_timer_key(
            timer_type=timer_type,
            chat_id=chat_id,
            player_id=player_id,
        )

        timer = EventTimer(timer_key, timeout, event, *args, **kwargs)
        timer.start()
        self._timers[timer_key] = timer

    def create_interval_timer(
        self,
        timer_type: str,
        chat_id: int,
        event: Callable[..., Awaitable[Any]],
        player_id: int | None = None,
        timeout: int = 30,
        interval: int = 5,
        *args,
        **kwargs,
    ):
        timer_key = self._get_timer_key(
            timer_type=timer_type,
            chat_id=chat_id,
            player_id=player_id,
        )

        timer = IntervalEventTimer(timer_key, timeout, interval, event, *args, **kwargs)
        timer.start()
        self._timers[timer_key] = timer

    def cancel_timer(
        self,
        timer_type: str,
        chat_id: int,
        player_id: int = None,
    ) -> bool:
        timer_key = self._get_timer_key(timer_type, chat_id, player_id)

        if timer_key in self._timers:
            self._timers[timer_key].cancel()
            del self._timers[timer_key]
            return True
        return False


timer_manager = TimersManager()
