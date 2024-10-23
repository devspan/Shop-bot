import logging
from aiogram import Bot
from aiogram.types import Message, ReplyKeyboardMarkup
from loader import dp, db
from filters import IsAdmin, IsUser
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, ChatActions
from keyboards.default.markups import all_right_message, back_markup, cancel_message
from states import NotificationState, SosState
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from PIL import Image
import io


# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Menu options
catalog = '🛍️ Parduotuvė'
cart = '🛒 Perziureti krepseli'
sos = '💬 Palikti komentarą'
delivery_status = '🚚 Užsakymo statusas'
create_notification = '💰 Sukurti pranesima'
settings = '⚙️ Parduotuvės nustatymai'
orders = '📦 Užsakymai'
notifications = '💬 Skelbimai'

@dp.message_handler(IsUser(), text='🛒 My Orders')
async def process_orders(message: Message):
    orders = db.fetchall('SELECT * FROM orders WHERE cid=?', (message.chat.id,))
    
    if not orders:
        await message.answer('❌ Uzsakymu nera.')
        return
    
    response = ''
    for order in orders:
        order_id, cid, usr_name, usr_address, products, photo, status, order_date = order
        response += f"📦 <b>Order #{order_id}</b>\n"
        response += f"✔️Status: <b>{status}</b>\n"
        response += f"📅Date: <b>{order_date}</b>\n"
        response += f"🛒Products: <b>{products}</b>\n"
        response += f"💳Wallet: <b>{usr_address}</b>\n\n"
    
    await message.answer(response)


dp.message_handler(IsAdmin(), commands=['set_out_of_stock'])
async def set_out_of_stock(message: Message):
    parts = message.text.split(' ')
    product_id = parts[1]  # ID of the product to mark as out of stock

    db.query('UPDATE products SET stock = 0 WHERE idx=?', (product_id,))
    await message.answer(f"Product {product_id} marked as out of stock.")

# Admin update order status:
@dp.message_handler(IsAdmin(), commands=['update_status'])
async def update_order_status(message: Message):
    parts = message.text.split(' ')
    order_id = parts[1]  # The ID of the order to update
    new_status = parts[2]  # The new status (e.g., 'confirmed', 'shipped', 'delivered')

    db.query('UPDATE orders SET status=? WHERE id=?', (new_status, order_id))
    await message.answer(f"Order #{order_id} updated to {new_status}.")


@dp.message_handler(IsAdmin(), text=create_notification)
async def process_notification_start(message: Message, state: FSMContext):
    await SosState.submit.set()
    await message.answer("✏️ Pranesimo tekstas:", reply_markup=back_markup())


@dp.message_handler(IsAdmin(), state=SosState.submit)
async def process_notification(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['notification'] = message.text
        db.query('INSERT INTO notification (cid, notification) VALUES (?, ?)', (message.chat.id, data['notification']))
    await message.answer("📤 Pranesimas issiustas!", reply_markup=back_markup())
    await state.finish()


@dp.message_handler(IsAdmin(), text='💬 Peržiūrėti pranešimus')
async def process_questions(message: Message):
    questions = db.fetchall('SELECT * FROM questions')
    if len(questions) == 0:
        await message.answer('Nera komentaru.')
    else:
        for cid, question in questions:
            await message.answer(f'User ID: {cid} - {question}', reply_markup=back_markup())


@dp.message_handler(text=notifications)
async def process_messages(message: Message):
    notifications = db.fetchall('SELECT * FROM notification')  # Correctly call the query method
    if notifications:
        for cid, notification in notifications:
            await message.answer(notification, reply_markup=ReplyKeyboardMarkup())  
    else:
        await message.answer("Nera pranesimu", reply_markup=ReplyKeyboardMarkup())     


# Admin Menu
@dp.message_handler(IsAdmin(), commands='menu')
async def admin_menu(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(settings, orders)
    markup.add(create_notification, '💬 Peržiūrėti pranešimus')
    await message.answer('🛠️ Admin Meniu', reply_markup=markup)


@dp.message_handler(IsUser(), commands='menu')
async def user_menu(message: Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(catalog, cart)
    markup.add(delivery_status, sos)
    markup.add(notifications)
    markup.add("🔙 Atgal")  # Adding the back button directly here if needed
    await message.answer('📋 Vartotojo Meniu', reply_markup=markup)


# Handle the SOS request
@dp.message_handler(IsUser(), text=sos)
async def sos_handler(message: Message, state: FSMContext):
        async with state.proxy() as data:
            markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add(catalog, cart)
            markup.add(delivery_status, sos)
            markup.add(notifications)
        await SosState.question.set()  # Set the state for question
        await message.answer('📝<b>Atsiliepimai:</b> Rašykite savo klausimą ar komentarą:', reply_markup=markup)


# Process the question from the user
@dp.message_handler(state=SosState.question)
async def process_question(message: Message, state: FSMContext):    
    async with state.proxy() as data:
        data['question'] = message.text
    await process_submit(message, state)


# Error handling for invalid responses
@dp.message_handler(lambda message: message.text not in [cancel_message, all_right_message], state=SosState.submit)
async def process_price_invalid(message: Message):
    await message.answer('Klaida. Prašome pasirinkti teisingą variantą.')


# Handle cancel action
@dp.message_handler(text=cancel_message, state=SosState.submit)
async def process_cancel(message: Message, state: FSMContext):
    await message.answer('❌ Atsaukti!', reply_markup=ReplyKeyboardMarkup())
    await state.finish()


async def process_submit(message: Message, state: FSMContext):
    cid = message.chat.id

    async with state.proxy() as data:
        # Insert the question into the database
        db.query('INSERT INTO questions (cid, question) VALUES (?, ?)', (cid, data['question']))

    await message.answer('✔️ Komentaras išsiųstas!', reply_markup=ReplyKeyboardMarkup())  # Ensure back button is present
    await state.finish()
    await user_menu(message) 

def back_markup():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(KeyboardButton("👈 Atgal"))  # Your back button's text
    return markup
    
def send_resized_image(message :Message, image_data):
    image = Image.open(io.BytesIO(image_data))  # Open the image from bytes
    resized_image = image.resize((200, 200))  # Resize the image to 200x200px
    byte_io = io.BytesIO()
    resized_image.save(byte_io, format='PNG')  # Save the resized image to BytesIO
    byte_io.seek(0)
    Bot.send_photo(self=Bot ,chat_id=message.chat.id, photo=byte_io)
    return resized_image