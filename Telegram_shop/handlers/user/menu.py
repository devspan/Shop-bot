
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from loader import dp
from filters import IsAdmin, IsUser

catalog = '🛍️ Parduotuve'
balance = '💰 Баланс'
cart = '🛒 Krepselis'
delivery_status = '🚚 Uzsakymu busena'

settings = '⚙️ Redaguoti kataloga'
orders = '📦 Uzsakymai'
questions = '❓ Klausimai'

help = '❓ Pagalba'


@dp.message_handler(IsAdmin(), commands='menu')
async def admin_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(settings)
    markup.add(questions, orders)

    await message.answer('Meniu', reply_markup=markup)

@dp.message_handler(IsUser(), commands='menu')
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(selective=True)
    markup.add(catalog)
    markup.add(balance, cart)
    markup.add(delivery_status)
    markup.add(help)

    await message.answer('Meniu', reply_markup=markup)
