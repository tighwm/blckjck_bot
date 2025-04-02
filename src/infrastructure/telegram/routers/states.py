from aiogram.fsm.state import StatesGroup, State


class ChatState(StatesGroup):
    lobby = State()
    bid = State()
    game = State()
