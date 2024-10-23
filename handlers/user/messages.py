# from loader import db
# from aiogram.types import Message
# from aiogram.dispatcher import FSMContext
# from loader import dp, db

# @dp.message_handler(text="messages")
# async def process_messages(message: Message, state: FSMContext):
#         notifications = db.query('SELECT * FROM notification')  # Correctly call the query method
#         if(notifications):
#             for notification in notifications:
#                  message.answer(notification)  
#         else:
#               message.answer("Nera pranesimu")     
            
