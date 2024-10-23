# from aiogram.dispatcher import FSMContext
# from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
# from filters.is_user import IsUser
# from keyboards.default.markups import all_right_message, back_markup, cancel_message, submit_markup
# from aiogram.types import Message
# from states import SosState
# from loader import dp, db
# from .menu import sos, user_menu

# @dp.message_handler(IsUser(), text=sos)
# async def sos_handler(message: Message, state: FSMContext):
#     await SosState.question.set()  # Set the state for question
#     await message.answer('Rašykite savo klausimą ar komentarą:', reply_markup=back_markup())

# # Process the question from the user
# @dp.message_handler(state=SosState.question)
# async def process_question(message: Message, state: FSMContext):    
#     async with state.proxy() as data:
#         data['question'] = message.text
#     await process_submit(message, state)

# # Error handling for invalid responses
# @dp.message_handler(lambda message: message.text not in [cancel_message, all_right_message], state=SosState.submit)
# async def process_price_invalid(message: Message):
#     await message.answer('Klaida. Prašome pasirinkti teisingą variantą.')

# # Handle cancel action
# @dp.message_handler(text=cancel_message, state=SosState.submit)
# async def process_cancel(message: Message, state: FSMContext):
#     await message.answer('Atsaukti!', reply_markup=back_markup())
#     await state.finish()

# # Handle the submission of the question
# @dp.message_handler(text=all_right_message, state=SosState.submit)
# async def process_submit(message: Message, state: FSMContext):
#     cid = message.chat.id

#     async with state.proxy() as data:
#         # Insert the question into the database
#         db.query('INSERT INTO questions VALUES (?, ?)', (cid, data['question']))
        
#     await message.answer('💬 Komentaras išsiųstas!', reply_markup=back_markup())
#     await state.finish()
#     await user_menu(message)
