from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData
from loader import db

product_cb = CallbackData('product', 'id', 'action')


def product_markup(idx='', price=0):

    global product_cb

    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton(f'Prideti i krepseli - {price}eu.', callback_data=product_cb.new(id=idx, action='add'),row_width=1))

    return markup