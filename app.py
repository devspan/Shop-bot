import os
from queue import Full
import handlers
from aiogram import executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from data import config
from loader import dp, db, bot
import filters
import logging
from utils.notify_admins import on_startup_notify

filters.setup(dp)

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 5000))
user_message = 'Klientas'
admin_message = 'NevisadaAs'

ADMIN_COMMAND = os.getenv("ADMIN_COMMAND", "/admin")  # Default to "/admin" if not set


@dp.message_handler(lambda message: message.text and message.text.lower() == ADMIN_COMMAND.lower())
async def admin_mode(message):
    await message.answer('Admin mode activated')


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    # You can replace SHOP_IMAGE_URL with your actual image URL
    SHOP_IMAGE_URL = "YOUR_SHOP_IMAGE_URL_HERE"
    
    welcome_text = (
        '🌟 Welcome to our Store! 🌟\n\n'
        '📜 Important Information:\n'
        '• Use /menu to browse our catalog\n'
        '• Secure payment options available at checkout\n'
        '• Customer support available 24/7\n\n'
        '⚠️ <b>Disclaimer: This service is intended for educational purposes only.</b>\n\n'
        '💡 Need help? Use our "Contact Support" option for assistance.'
    )
    
    # Send image first (if you have one)
    # await message.answer_photo(photo=SHOP_IMAGE_URL)
    
    # Send welcome text
    await message.answer(welcome_text, parse_mode='HTML')


async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)
    await on_startup_notify(dp)
    db.create_tables()
    await bot.delete_webhook()
    if config.WEBHOOK_URL:
        await bot.set_webhook(config.WEBHOOK_URL)

async def on_shutdown():
    logging.warning("Shutting down..")

    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    logging.warning("Bot down")


if __name__ == '__main__':

    if (("HEROKU_APP_NAME" in list(os.environ.keys())) or
        ("RAILWAY_PUBLIC_DOMAIN" in list(os.environ.keys()))):

        executor.start_webhook(
            dispatcher=dp,
            webhook_path=config.WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )

    else:

        executor.start_polling(dp, on_startup=on_startup, skip_updates=False)
