from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def game_btns():
    hit = InlineKeyboardButton(text="Взять карту", callback_data="hit")
    stand = InlineKeyboardButton(text="Абоба", callback_data="stand")
    row = [hit, stand]
    rows = [row]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup
