from aiogram.dispatcher.filters.state import StatesGroup, State

class CheckoutState(StatesGroup):
    check_cart = State()
    name = State()
    image = State()
    address = State()
    #comment = State()
    confirm = State()