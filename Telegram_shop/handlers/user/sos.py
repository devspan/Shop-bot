
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from keyboards.default.markups import all_right_message, cancel_message, submit_markup
from aiogram.types import Message
from states import SosState
from filters import IsUser
from loader import dp, db
from .menu import help, balance, cart, catalog, delivery_status


@dp.message_handler(IsUser(), text=help)
async def process_sos(message: Message, state: FSMContext):
    await SosState.question.set()
    await message.answer('Rašykite savo problema kuo detaliau.', reply_markup=ReplyKeyboardRemove())


@dp.message_handler(state=SosState.question)
async def process_question(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text
    await message.answer('Patvirtinkite ar viskas teisingai.', reply_markup=submit_markup())
    await SosState.next()


@dp.message_handler(lambda message: message.text not in [cancel_message, all_right_message], state=SosState.submit)
async def process_price_invalid(message: Message):
    await message.answer('Klaida.')


@dp.message_handler(text=cancel_message, state=SosState.submit)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('Atsaukta!', reply_markup=ReplyKeyboardRemove())
    await state.finish()


@dp.message_handler(text=all_right_message, state=SosState.submit)
async def process_submit(message: Message, state: FSMContext):

    cid = message.chat.id

    if db.fetchone('SELECT * FROM questions WHERE cid=?', (cid,)) == None:

        async with state.proxy() as data:
            db.query('INSERT INTO questions VALUES (?, ?)',
                     (cid, data['question']))
            
        markup = ReplyKeyboardMarkup(selective=True)
        markup.add(catalog)
        markup.add(balance, cart)
        markup.add(delivery_status)
        markup.add(help)
        await message.answer('Issiusta!', reply_markup=markup)

    else:

        await message.answer('Pabandikite veliau, suveike apsauga nuo spamo.', reply_markup=ReplyKeyboardRemove())

    await state.finish()
