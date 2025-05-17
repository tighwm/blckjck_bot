from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from infrastructure.telegram.middlewares import (
    SaveUserDB,
    AntiFlood,
    CommandServiceGetter,
)
from application.services import CommandService
from utils.tg.functions import format_user_profile

router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(SaveUserDB())
router.message.middleware(CommandServiceGetter())


@router.message(Command("start"))
async def handle_start(message: Message):
    await message.answer("Да живой я блять.")


@router.message(Command("profile"))
async def handle_profile(
    message: Message,
    com_service: CommandService,
):
    try:
        res = await com_service.get_user_profile(message.from_user.id)
    except Exception as e:
        await message.answer(e.__str__())
        return
    text = format_user_profile(res)
    await message.answer(text)


@router.message(Command("help"))
async def handle_help(message: Message):
    text = "Команда /lobby [секунд] к началу игры. (квадратные скобки не нужны)"
    await message.answer(text)
