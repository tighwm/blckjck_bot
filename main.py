import asyncio

from src.infrastructure.telegram.bot import TelegramBot

tgbot = TelegramBot()


async def main():
    await tgbot.start_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
