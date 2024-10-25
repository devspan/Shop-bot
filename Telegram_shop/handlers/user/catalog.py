
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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

add_to_cart_cb = CallbackData("cart", "action", "product_id")
expand_image_cb = CallbackData("expand", "product_id")


@dp.message_handler(IsUser(), text=catalog)
async def process_catalog(message: Message):
    await message.answer('Pasirinkite prekiu kategorija:',
                         reply_markup=categories_markup())


@dp.callback_query_handler(IsUser(), category_cb.filter(action='view'))
async def category_callback_handler(query: CallbackQuery, callback_data: dict):

    products = db.fetchall('''SELECT * FROM products product
    WHERE product.tag = (SELECT title FROM categories WHERE idx=?) 
    AND product.idx NOT IN (SELECT idx FROM cart WHERE cid = ?)''',
                           (callback_data['id'], query.message.chat.id))

    await query.answer('Prekiu sarasas:.')
    await show_products(query.message, products)

# Handler for "Add to Cart" button
@dp.callback_query_handler(add_to_cart_cb.filter(action="add"))
async def add_to_cart_callback_handler(query: CallbackQuery, callback_data: dict):
    product_id = callback_data["product_id"]
    db.query('INSERT INTO cart (cid, idx, quantity) VALUES (?, ?, 1)', (query.message.chat.id, product_id))
    
    await query.answer('Preke prideta i krepseli!')

@dp.callback_query_handler(IsUser(), product_cb.filter(action='add'))
async def add_product_callback_handler(query: CallbackQuery, callback_data: dict):

    db.query('INSERT INTO cart VALUES (?, ?, 1)',
             (query.message.chat.id, callback_data['id']))

    await query.answer('Preke prideta i krepseli!')
    await query.message.delete()


async def show_products(m, products):
    if len(products) == 0:
        await m.answer('Prekiu siuo metu nera 😢')
    else:
        await bot.send_chat_action(m.chat.id, ChatActions.TYPING)

        for idx, title, body, image, price, _ in products:
            # Prepare inline keyboard with "View Image" and "Add to Cart" buttons
            markup = product_markup(idx, price)
            markup.add(
                InlineKeyboardButton("🔍 Iskleisti nuotrauka", callback_data=expand_image_cb.new(product_id=idx)),
                InlineKeyboardButton("➕ Pridėti į krepšelį", callback_data=add_to_cart_cb.new(action="add", product_id=idx))
            )

            # Add line breaks for "margin top" effect
            text = f'\n\n<b>{title}</b>\n\n{body[:50]}'
            await m.answer(text, reply_markup=markup)


@dp.callback_query_handler(expand_image_cb.filter())
async def expand_image_callback_handler(query: CallbackQuery, callback_data: dict):
    product_id = callback_data["product_id"]
    product = db.fetchone('SELECT title, body, photo, price FROM products WHERE idx = ?', (product_id,))

    if product:
        title, body, image, price = product
        if image:
            img = Image.open(BytesIO(image))
            img.thumbnail((400, 400))

            img_io = BytesIO()
            img.save(img_io, format="JPEG")
            img_io.seek(0)

            # Inline keyboard for expanded view
            expanded_markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("➕ Pridėti į krepšelį", callback_data=add_to_cart_cb.new(action="add", product_id=product_id))
            )

            # Delete previous message and send expanded view
            await query.message.delete()
            await query.message.answer_photo(
                photo=InputFile(img_io, filename="expanded_image.jpg"),
                caption=f'\n\n<b>{title}</b>\n\n{body[:100]}',
                reply_markup=expanded_markup
            )
        else:
            await query.answer("No image available for this product.")