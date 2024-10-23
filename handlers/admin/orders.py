from io import BytesIO
from PIL import Image
from aiogram.types import InputFile, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from loader import dp, db, bot
from filters import IsAdmin
from handlers.user.menu import orders

# Create callback data format for marking an order as done
from aiogram.utils.callback_data import CallbackData
done_callback = CallbackData('order', 'order_id', 'action')

@dp.message_handler(IsAdmin(), text=orders)
async def process_orders(message: Message):
    # Fetch all orders from the database
    orders_data = db.fetchall('SELECT * FROM orders')
    
    if len(orders_data) == 0:
        await message.answer('Uzsakymu nera.')
    else:
        await order_answer(message, orders_data)

async def order_answer(message, orders):
    for order in orders:
        # Extract order details
        order_id = order[0]  # Assuming the first field is the order ID
        usr_name = order[1]
        usr_address = order[2]
        products = order[3]
        photo_data = order[4]  # The BLOB data of the photo, if available
        comment = order[5]
        order_status = order[6]
        order_date = order[7]

        # Prepare the order details
        order_details = (
            f'Apmokejimo nuoroda: <b>{usr_name}</b>\n'
            f'Komentaras: <b>{usr_address}</b>\n'
            f'Uzsakymo data: {order_date}\n'
            f'Statusas: {order_status}\n'
            'Produktai:\n'
        )

        # Split the products field, which may contain multiple product_id=quantity pairs
        product_items = products.split()    

        for item in product_items:
            product_id, quantity = item.split('=')
            # Fetch product details (name, price) from the 'products' table
            product = db.fetchone('SELECT title, price FROM products WHERE idx=?', (product_id,))
            
            if product:
                product_name, product_price = product
                total_price = int(quantity) * product_price
                order_details += f' - {product_name}: {quantity} pcs @ {product_price}€ each, Total: {total_price}€\n'

        # Inline keyboard button to mark the order as "Done"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Pažymėti kaip atlikta", callback_data=done_callback.new(order_id=order_id, action='done')))

        # If there's a photo, resize it and send it with the order details
        if photo_data:
            # Load the photo from the BLOB data
            photo = Image.open(BytesIO(photo_data))

            # Resize the photo to make it smaller
            max_size = (200, 200)  # Resize to a max of 200x200 pixels
            photo.thumbnail(max_size)

            # Save the resized photo to a BytesIO object
            resized_photo_io = BytesIO()
            photo.save(resized_photo_io, format="JPEG")
            resized_photo_io.seek(0)  # Reset the BytesIO cursor to the start

            # Send the resized photo along with the order details
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=InputFile(resized_photo_io, filename="resized_photo.jpg"),
                caption=order_details,
                parse_mode='HTML',
                reply_markup=markup  # Add the inline keyboard
            )
        else:
            # If there's no photo, just send the order details
            await message.answer(order_details, parse_mode='HTML', reply_markup=markup)

# Callback handler to mark the order as "Done"
@dp.callback_query_handler(done_callback.filter(action='done'))
async def mark_order_as_done(callback_query: CallbackQuery, callback_data: dict):
    order_id = callback_data['order_id']

    # Update the order status in the database
    db.query('UPDATE orders SET status = ? WHERE cid = ?', ('done', order_id))

    # Acknowledge the callback
    await callback_query.answer("Užsakymas pažymėtas kaip atliktas!")

    # Optionally edit the message to show that the order is done
    await bot.edit_message_caption(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        caption=f"✅ Užsakymas #{order_id} pažymėtas kaip atliktas.",
        parse_mode='HTML'
    )