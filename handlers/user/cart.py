import datetime
import logging
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline.products_from_cart import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from keyboards.default.markups import *
from aiogram.types.chat import ChatActions
from states import CheckoutState
from loader import dp, db, bot
from filters import IsUser
from states.product_state import ProductState
from .menu import cart
from io import BytesIO
from PIL import Image
from aiogram.types import InputFile

@dp.message_handler(IsUser(), text=cart)
async def process_cart(message: Message, state: FSMContext):
    cart_data = db.fetchall('SELECT * FROM cart WHERE cid=?', (message.chat.id,))
    
    if not cart_data:
        await message.answer('Cart is empty.')
        return

    total_cost = 0
    async with state.proxy() as data:
        data['products'] = {}

    for _, product_id, quantity in cart_data:
        product = db.fetchone('SELECT * FROM products WHERE idx=?', (product_id,))
        if product:
            _, title, body, image_data, price, _ = product
            total_cost += price * quantity

            async with state.proxy() as data:
                data['products'][product_id] = [title, price, quantity]

            markup = product_markup(product_id, quantity)
            text = f'🛍 <b>{title}</b>\n\n{body}\n\n💸 Price: <b>{price}€</b>\nQuantity: {quantity}'
            
            if image_data:
                image = Image.open(BytesIO(image_data))
                max_size = (200, 200)
                image.thumbnail(max_size)

                resized_image_io = BytesIO()
                image.save(resized_image_io, format="JPEG")
                resized_image_io.seek(0)

                await message.answer_photo(
                    photo=InputFile(resized_image_io, filename="resized_image.jpg"),
                    caption=text,
                    reply_markup=markup
                )
            else:
                await message.answer(text, reply_markup=markup)

    if total_cost > 0:
        markup = ReplyKeyboardMarkup(resize_keyboard=True).add('📦 Checkout').add('🔙 Back')
        await message.answer(f'Total: <b>{total_cost}€</b>. Would you like to checkout?', reply_markup=markup)



@dp.callback_query_handler(IsUser(), product_cb.filter(action='increase'))
@dp.callback_query_handler(IsUser(), product_cb.filter(action='decrease'))
async def update_cart(query: CallbackQuery, callback_data: dict,  state: FSMContext):
    async with state.proxy() as data:

        product_id = callback_data['id']
        action = callback_data['action']

        current_quantity = db.fetchone('SELECT quantity FROM cart WHERE cid=? AND idx=?', (query.message.chat.id, product_id))[0]

        if action == 'increase':
            new_quantity = current_quantity + 1
        elif action == 'decrease' and current_quantity > 1:
            new_quantity = current_quantity - 1
        else:
            await query.answer('Minimum quantity is 1.')
        return
    db.query('UPDATE cart SET quantity=? WHERE cid=? AND idx=?', (new_quantity, query.message.chat.id, product_id))
    # Update the cart view
    await process_cart(query.message, state)


@dp.message_handler(IsUser(), text='📦 Checkout')
async def process_checkout(message: Message, state: FSMContext):
    await CheckoutState.check_cart.set()
    await checkout(message, state)


async def checkout(message: Message, state: FSMContext):
    answer = ''
    total_price = 0

    async with state.proxy() as data:
        for title, price, count_in_cart in data['products'].values():
            tp = count_in_cart * price
            answer += f'<b>{title}</b> * {count_in_cart}vnt. - 💰<b>{tp}€</b>\n'
            total_price += tp

    await message.answer(f'{answer}\n💶 Galutinė kaina: <b>{total_price}€</b>.', reply_markup=check_markup())


@dp.message_handler(IsUser(), lambda message: message.text not in [all_right_message, back_message], state=CheckoutState.check_cart)
async def process_check_cart_invalid(message: Message):
    await message.reply('Error.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.check_cart)
async def process_check_cart_back(message: Message, state: FSMContext):
    await state.finish()
    await process_cart(message, state)


@dp.message_handler(IsUser(), text=all_right_message, state=CheckoutState.check_cart)
async def process_check_cart_all_right(message: Message, state: FSMContext):
    await CheckoutState.next()
    await message.answer('💳 Enter your wallet address.', reply_markup=back_markup())


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.name)
async def process_name_back(message: Message, state: FSMContext):
    async with state.proxy() as data:
        await message.answer('Are you sure you want to change the address from <b>' + data['name'] + '</b>?', reply_markup=back_markup())
    await CheckoutState.name.set()


@dp.message_handler(IsUser(), state=CheckoutState.name)
async def process_name(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text #name pinigines adresas
    await CheckoutState.next()
    await message.answer('📷 Upload payment confirmation photo.', reply_markup=back_markup())


from io import BytesIO
from PIL import Image
import logging
from aiogram import types
from aiogram.dispatcher import FSMContext

@dp.message_handler(IsUser(), content_types=['photo'], state=CheckoutState.image)
async def process_image_photo(message: types.Message, state: FSMContext):
    try:
        # Get the highest resolution photo
        file_id = message.photo[-1].file_id
        file_info = await bot.get_file(file_id)
        
        # Download the file from Telegram's servers as a bytes-like object
        file_data = await bot.download_file(file_info.file_path)
        
        # Create a BytesIO object from the downloaded file data
        file_bytes_io = BytesIO(file_data.read())  # Ensure you're getting bytes
        
        # Load the image from the BytesIO object
        image = Image.open(file_bytes_io)
        
        # Resize the image (max 200x200 pixels)
        max_size = (200, 200)
        image.thumbnail(max_size)
        
        # Save the resized image to a BytesIO object
        resized_image_io = BytesIO()
        image.save(resized_image_io, format="JPEG")
        resized_image_io.seek(0)  # Reset the BytesIO cursor to the start
        
        # Store the resized image as raw bytes in FSM context
        async with state.proxy() as data:
            data['image'] = resized_image_io.getvalue()  # Get raw bytes
        
        # Proceed to the next state
        await CheckoutState.next()
        await message.answer('Additional Notes', reply_markup=back_markup())

    except Exception as e:
        logging.error(f"Error in process_image_photo: {e}")
        await message.answer("Įvyko klaida įkeliant nuotrauką. Bandykite dar kartą.")



@dp.message_handler(IsUser(), state=CheckoutState.image)
async def process_image_url(message: Message, state: FSMContext):
    if message.text == back_message:
        await ProductState.body.set()
        async with state.proxy() as data:
            await message.answer(f"Go back?", reply_markup=back_markup())
    else:
        await message.answer('Please upload a photo.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.address)
async def process_address_back(message: Message, state: FSMContext):
    async with state.proxy() as data:
        await message.answer('Are you sure you want to change the address from <b>' + data['name'] + '</b>?', reply_markup=back_markup())
    await CheckoutState.name.set()


@dp.message_handler(IsUser(), state=CheckoutState.address)
async def process_address(message: Message, state: FSMContext):
    async with state.proxy() as data:
        data['address'] = message.text

    await confirm(message)
    await CheckoutState.next()


async def confirm(message: Message):
    await message.answer(f'⚠️ Please verify all details and confirm your order.', reply_markup=confirm_markup())


@dp.message_handler(IsUser(), lambda message: message.text not in [confirm_message, back_message], state=CheckoutState.confirm)
async def process_confirm_invalid(message: Message):
    await message.reply('Error.')


@dp.message_handler(IsUser(), text=back_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    await CheckoutState.address.set()
    async with state.proxy() as data:
        await message.answer('Are you sure you want to change the address from <b>' + data['address'] + '</b>?', reply_markup=back_markup())


@dp.message_handler(IsUser(), text=confirm_message, state=CheckoutState.confirm)
async def process_confirm(message: Message, state: FSMContext):
    markup = ReplyKeyboardRemove()

    logging.info('Order confirmed.')
    async with state.proxy() as data:
        cid = message.chat.id
        username = message.from_user.username if message.from_user.username else "N/A"

        products = [f"{idx}={quantity}" for idx, quantity in db.fetchall('SELECT idx, quantity FROM cart WHERE cid=?', (cid,))]

        if 'image' in data:
            image_data = data['image']
            db.query('INSERT INTO orders (cid, usr_name, usr_address, usr_username, products, photo, status, order_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (cid, data['name'], data['address'], username, ' '.join(products), image_data, 'pending', datetime.datetime.now().date()))
        else:    
            db.query('INSERT INTO orders (cid, usr_name, usr_address, usr_username, products, status, order_date) VALUES (?, ?, ?, ?, ?, ?, ?) ',
                (cid, data['name'], data['address'], username, ' '.join(products), 'pending', datetime.datetime.now().date()))

        db.query('DELETE FROM cart WHERE cid=?', (cid,))

    address = data.get('address', 'N/A')
    message_content = f'Delivery Address: <b>{address}</b>'
    logging.info(f"Sending message: {message_content}")

    await message.answer(message_content, reply_markup=markup)
    await state.finish()