from aiogram.dispatcher.filters.state import StatesGroup, State

class NotificationState(StatesGroup):
    input_text = State()
    submit = State()