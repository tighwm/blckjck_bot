from abc import ABC, abstractmethod


class TelegramBotInterface(ABC):
    @abstractmethod
    async def handle_bid(self, message):
        """Обработка ставки"""
        pass

    @abstractmethod
    async def handle_start_game(self, message):
        """Обработка начала новой игры"""
        pass

    @abstractmethod
    async def handle_hit(self, callback_query):
        """Обработка действия 'Взять карту'"""
        pass

    @abstractmethod
    async def handle_stand(self, callback_query):
        """Обработка действия 'Достаточно'"""
        pass

    @abstractmethod
    async def handle_leave(self, message):
        """Обработка выхода из действующей игры"""
        pass
