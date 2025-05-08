from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from infrastructure.telegram.middlewares import (
    SaveUserDB,
    AntiFlood,
    UserServiceGetter,
)
from application.services import UserService
from utils.tg_utils import format_user_profile

router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(SaveUserDB())
router.message.middleware(UserServiceGetter())


@router.message(Command("start"))
async def handle_start(message: Message):
    await message.answer("Да живой я блять.")


@router.message(Command("profile"))
async def handle_profile(
    message: Message,
    user_service: UserService,
):
    try:
        res = await user_service.get_user_profile(message.from_user.id)
    except Exception as e:
        await message.answer(e.__str__())
        return
    text = format_user_profile(res)
    await message.answer(text)
