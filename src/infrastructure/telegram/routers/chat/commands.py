from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from infrastructure.telegram.middlewares import (
    SaveUserDB,
    AntiFlood,
    CommandServiceGetter,
)
from application.services import CommandService
from application.services.command import ResponseType, Response
from utils.tg.functions import format_user_profile

router = Router()
router.message.middleware(AntiFlood())
router.message.middleware(SaveUserDB())
router.message.middleware(CommandServiceGetter())


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


async def process_unsuccessful(message: Message, response: Response):
    if response.type == ResponseType.TOO_EARLY_FOR_BONUS:
        await message.answer(f"Попробуйте через {response.data.get("cooldown")}.")
    elif response.type == ResponseType.ONLY_BELLOW_FIVE_BALANCE:
        await message.answer("Только при балансе ниже 5.")


@router.message(Command("bonus"))
async def handle_bonus(
    message: Message,
    com_service: CommandService,
):
    res = await com_service.give_bonus(user_id=message.from_user.id)

    if res.success is False:
        return await process_unsuccessful(
            message=message,
            response=res,
        )

    await message.answer("Ежедневный бонус в размере 125 выдан.")
