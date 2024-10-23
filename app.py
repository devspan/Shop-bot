
import os
from queue import Full
import handlers
from aiogram import executor, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from data import config
from loader import dp, db, bot
import filters
import logging

filters.setup(dp)

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 5000))
user_message = 'Klientas'
admin_message = 'NevisadaAs'


@dp.message_handler(lambda message: message.text and os.environ.get("admin") in message.text.lower())
async def admin_handler(message: types.Message):
    cid = message.chat.id
    if cid not in config.ADMINS:
        config.ADMINS.append(cid)
        await message.answer('Added to admins! 👋')
    else:
        if cid in config.ADMINS:
            config.ADMINS.remove(cid)
            await message.answer('Added to users! 👋')


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer(
        'Sveiki! 👋\n'
        '🔞 <b>Botas skirtas mokymosi tikslams. Nepropaguojame narkotinių medžiagų platinimo</b>❗️ \n\n'
        '📌 <b>Atidaryti/Pastringo meniu?</b> - rašykite komandą /meniu.\n'
        '📌 <b>Sąskaita apmokėjimui</b> - bus pateikta atliekant užsakymą.\n'
        '📌 <b>Apmokėjau, bet nepavyksta užbaigti užsakymo</b> - spauskite mygtuką "Susisiekti" ir detaliai paaiškinkite problemą.',
        parse_mode='HTML')


async def on_startup(dp):
    logging.basicConfig(level=logging.INFO)
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
