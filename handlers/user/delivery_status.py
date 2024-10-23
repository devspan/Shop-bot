from aiogram.types import Message
from loader import dp, db
from .menu import delivery_status
from filters import IsUser

@dp.message_handler(IsUser(), text=delivery_status)
async def process_delivery_status(message: Message):
    # Fetch the user's orders based on chat id (user id)
    orders = db.fetchall('SELECT * FROM orders WHERE cid=?', (message.chat.id,))
    
    if len(orders) == 0:
        await message.answer('Uzsakymu nera.')
    else:
        await delivery_status_answer(message, orders)

async def delivery_status_answer(message, orders):
    res = ''

    for order in orders:
        # Extract order information
        usr_name = order[1]  # Assuming this is the user's name
        products = order[3]  # Assuming this stores the product info (e.g., product_id=quantity)

        # Add the order number and user name to the response
        res += f'Uzsakymas <b>№{order[0]}</b> nuo <b>{usr_name}</b>\n'
        
        # Translate the order status into readable text

        res += f'<b>Statusas:</b> ✔️ Uzsakymas priimtas ir ruosiamas.\n'
        # Split the products field (product_id=quantity pairs) and process each product
        product_items = products.split()

        res += '🛒 Produktai:\n'
        for item in product_items:
            product_id, quantity = item.split('=')
            product = db.fetchone('SELECT title, price FROM products WHERE idx=?', (product_id,))
            
            if product:
                product_name, product_price = product
                total_price = int(quantity) * product_price
                res += f' - {product_name}: {quantity} vnt. @ {product_price}€ uz vnt., Viso: {total_price}€\n'
        
        res += '\n'  # Add spacing between orders

    await message.answer(res, parse_mode='HTML')
