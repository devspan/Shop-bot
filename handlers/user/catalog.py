
import logging
from aiogram.types import Message, CallbackQuery
from keyboards.inline.categories import categories_markup, category_cb
from keyboards.inline.products_from_catalog import product_markup, product_cb
from aiogram.utils.callback_data import CallbackData
from aiogram.types.chat import ChatActions
from loader import dp, db, bot
from .menu import catalog
from filters import IsUser
from io import BytesIO
from PIL import Image
from aiogram.types import InputFile
from loader import bot

@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    await message.answer('🔍 Pasirinkite kategorija:',
                         reply_markup=categories_markup())


@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):

    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))

    await query.answer('🛒 Prekiu sarasas.')
    await show_products(query.message, products)


@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery, callback_data: dict):

    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))

    await query.answer('✔️ Preke prideta i krepseli!')


async def show_products(m :Message, products):
    if len(products) == 0:
        await m.answer('Tuscia 😢')
    else:
        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        for idx, title, body, image_data, price, _ in products:
            markup = product_markup(idx, price)
            text = f'<b>{title}</b>\n\n{body}'

            # If there's an image, resize it before sending
            if image_data:
                # Load the image from the BLOB data
                image = Image.open(BytesIO(image_data))

                # Resize the image to make it smaller
                max_size = (200, 200)  # Resize to a max of 200x200 pixels
                image.thumbnail(max_size)

                # Save the resized image to a BytesIO object
                resized_image_io = BytesIO()
                image.save(resized_image_io, format="JPEG")
                resized_image_io.seek(0)  # Reset the BytesIO cursor to the start

                # Send the resized image along with the product details
                await m.answer_photo(
                    photo=InputFile(resized_image_io, filename="resized_image.jpg"),
                    caption=text,
                    reply_markup=markup
                )
            else:
                # If no image, just send the product details
                await m.answer(text, reply_markup=markup)