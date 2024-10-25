from io import BytesIO
from PIL import Image
from aiogram.types import InputFile, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from loader import dp, db, bot
from filters import IsAdmin
from aiogram.utils.callback_data import CallbackData
from handlers.user.menu import orders

done_callback = CallbackData('order', 'order_id', 'action')
status_callback = CallbackData('status', 'status')

@dp.message_handler(IsAdmin(), text=orders)  # Change this to your trigger text
async def process_orders(message: Message):
    # Create inline keyboard for status selection
    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("Visi užsakymai", callback_data=status_callback.new(status='all')),
        InlineKeyboardButton("Neatlikti užsakymai", callback_data=status_callback.new(status='pending')),
        InlineKeyboardButton("Atlikti užsakymai", callback_data=status_callback.new(status='done')),
    )
    
    await message.answer("Pasirinkite užsakymų statusą.", reply_markup=keyboard)


@dp.callback_query_handler(status_callback.filter())
async def filter_orders(callback_query: CallbackQuery, callback_data: dict):
    status = callback_data['status']

    # Fetch orders based on the selected status
    if status == 'all':
        orders_data = db.fetchall('SELECT * FROM orders')  # Fetch all orders
    else:
        orders_data = db.fetchall('SELECT * FROM orders WHERE status = ?', (status,))  # Fetch orders by status
    
    if not orders_data:
        await callback_query.answer('Užsakymų nėra 🤷', show_alert=True)
        return

    await order_answer(callback_query.message, orders_data)

async def order_answer(message: Message, orders):
    # Create inline keyboard for status selection
    keyboard = InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("Visi užsakymai", callback_data=status_callback.new(status='all')),
        InlineKeyboardButton("Neatlikti užsakymai", callback_data=status_callback.new(status='pending')),
        InlineKeyboardButton("Atlikti užsakymai", callback_data=status_callback.new(status='done')),
    )
    
    for order in orders:
        order_id = order[0]  # Assuming the first field is the order ID
        usr_name = order[1]
        usr_address = order[2]
        products = order[3]
        photo_data = order[4]  # The BLOB data of the photo, if available
        comment = order[5]
        order_status = order[6]
        order_date = order[7]
        usr_username = order[8]

        # Prepare the order details
        if order_status == 'done':
            order_details = (
                f'🙂Uzsakovas: {usr_username}\n'
                f"📅 Užsakymo data: {order_date}\n"
                f"Užsakymas atliktas✅\n"
            )
            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Išskleisti ▼", callback_data=done_callback.new(order_id=order_id, action='expand')),
                InlineKeyboardButton("Visi užsakymai", callback_data=status_callback.new(status='all')),
                InlineKeyboardButton("Neatlikti užsakymai", callback_data=status_callback.new(status='pending')),
                InlineKeyboardButton("Atlikti užsakymai", callback_data=status_callback.new(status='done')),
            )
        else:
            order_details = (
                f'🙂Uzsakovas: {usr_username}\n'
                f'🔗Apmokėjimo nuoroda: <b>{usr_name}</b>\n'
                f'💬Komentaras: <b>{usr_address}</b>\n'
                f'📅Užsakymo data: {order_date}\n'
                f'Užsakymas neatliktas❌\n\n'
                'Produktai:\n'
            )

            # Split the products field
            product_items = products.split()    

            for item in product_items:
                product_id, quantity = item.split('=')
                product = db.fetchone('SELECT title, price FROM products WHERE idx=?', (product_id,))
                
                if product:
                    product_name, product_price = product
                    total_price = int(quantity) * product_price
                    order_details += f' - {product_name}: {quantity} vnt @ {product_price}€ kiekvienam, Iš viso: {total_price}€\n'

            markup = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Pažymėti kaip atlikta ✅", callback_data=done_callback.new(order_id=order_id, action='done')),
                InlineKeyboardButton("Visi užsakymai", callback_data=status_callback.new(status='all')),
                InlineKeyboardButton("Neatlikti užsakymai", callback_data=status_callback.new(status='pending')),
                InlineKeyboardButton("Atlikti užsakymai", callback_data=status_callback.new(status='done')),
            )

        # If there's a photo, resize it and send it with the order details
        if photo_data:
            try:
                photo = Image.open(BytesIO(photo_data))
                max_size = (200, 200)
                photo.thumbnail(max_size)

                resized_photo_io = BytesIO()
                photo.save(resized_photo_io, format="JPEG")
                resized_photo_io.seek(0)

                await bot.send_photo(
                    chat_id=message.chat.id,
                    photo=InputFile(resized_photo_io, filename="resized_photo.jpg"),
                    caption=order_details,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except Exception as e:
                await message.answer("Klaida apdorojant nuotrauką.")
                print(f"Photo processing error: {e}")
        else:
            await message.answer(order_details, parse_mode='HTML', reply_markup=markup)

# Callback handler to mark the order as "Done" or to expand/collapse
@dp.callback_query_handler(done_callback.filter())
async def handle_order_callback(callback_query: CallbackQuery, callback_data: dict):
    order_id = callback_data['order_id']
    action = callback_data['action']

    if action == 'done':
        try:
            db.query('UPDATE orders SET status = ? WHERE cid = ?', ('done', order_id))
            await callback_query.answer("Užsakymas pažymėtas kaip atliktas!✅")
            await bot.edit_message_caption(
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                caption=f"<b>Užsakymas atliktas</b> ✅",
                parse_mode='HTML'
            )
        except Exception as e:
            await callback_query.answer("Nepavyko pažymėti užsakymo kaip atlikto.")
            print(f"Update error: {e}")

    elif action in ['expand', 'collapse']:
        order = db.fetchone('SELECT * FROM orders WHERE cid = ?', (order_id,))
        if order:
            usr_name = order[1]
            usr_address = order[2]
            products = order[3]
            order_date = order[7]
            
            if action == 'expand':
                order_details = (
                    f"✅ Užsakymas #{order_id} atliktas\n"
                    f"🔗 Apmokėjimo nuoroda: <b>{usr_name}</b>\n"
                    f"💬 Komentaras: <b>{usr_address}</b>\n"
                    f"📅 Užsakymo data: {order_date}\n\n"
                    "Produktai:\n"
                )

                product_items = products.split()    
                for item in product_items:
                    product_id, quantity = item.split('=')
                    product = db.fetchone('SELECT title, price FROM products WHERE idx=?', (product_id,))
                    if product:
                        product_name, product_price = product
                        total_price = int(quantity) * product_price
                        order_details += f' - {product_name}: {quantity} vnt @ {product_price}€ kiekvienam, Iš viso: {total_price}€\n'

                markup = InlineKeyboardMarkup().add(
                    InlineKeyboardButton("Slėpti detales", callback_data=done_callback.new(order_id=order_id, action='collapse')),
                    InlineKeyboardButton("Visi užsakymai", callback_data=status_callback.new(status='all')),
                    InlineKeyboardButton("Neatlikti užsakymai", callback_data=status_callback.new(status='pending')),
                    InlineKeyboardButton("Atlikti užsakymai", callback_data=status_callback.new(status='done')),
                )
                await bot.edit_message_caption(
                    chat_id=callback_query.message.chat.id,
                    message_id=callback_query.message.message_id,
                    caption=order_details,
                    parse_mode='HTML',
                    reply_markup=markup
                )

            elif action == 'collapse':
                order_details = (
                    f"Užsakymas atliktas✅\n"
                    f"📅 Užsakymo data: {order_date}\n"
                )
                markup = InlineKeyboardMarkup().add(
                    InlineKeyboardButton("Rodyti detaliai", callback_data=done_callback.new(order_id=order_id, action='expand')),
                    InlineKeyboardButton("Visi užsakymai", callback_data=status_callback.new(status='all')),
                    InlineKeyboardButton("Neatlikti užsakymai", callback_data=status_callback.new(status='pending')),
                    InlineKeyboardButton("Atlikti užsakymai", callback_data=status_callback.new(status='done')),
                )
                await bot.edit_message_caption(
                    chat_id=callback_query.message.chat.id,
                    message_id=callback_query.message.message_id,
                    caption=order_details,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        else:
            await callback_query.answer("Nepavyko rasti užsakymo.")
