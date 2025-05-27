from aiogram import Router
from aiogram.filters import Command, ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER
from aiogram.types import Message, ChatMemberUpdated

from infrastructure.telegram.middlewares import AntiFlood

router = Router()
router.message.middleware(AntiFlood())


@router.message(Command("start"))
async def handle_start(message: Message):
    await message.answer("👻👻🌼.")


@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def handle_join_bot_to_chat(event: ChatMemberUpdated):
    await event.answer("Для того, что-бы начать игру, отправьте команду /lobby")
