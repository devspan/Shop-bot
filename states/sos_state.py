from aiogram.dispatcher.filters.state import StatesGroup, State

class SosState(StatesGroup):
    question = State()
    confirm = State()
    submit = State()
