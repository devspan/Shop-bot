
import os
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
user_message = 'Пользователь'
admin_message = 'Админ'


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):

    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(user_message, admin_message)

    await message.answer('''Привет! 👋

TEMP-NAME Pardotuve.

            🔞 <b>Botas skirtas mokymosi tikslams visos nuotraukos ikeltos is interneto saltyniu. Nepropaguojame narkotinių medžiagų platinimo ir vartojimo</b>❗️ \n\n'

🛍️ Kad pradeti irasykite komanda /menu.

❓ Jeigu turite klausimu arba susidurete su problemom pasirinkite 'Pagalba' mygtuka is meniu.
                         
📌 <b>Atidaryti/Pastringo meniu?</b> - rašykite komandą /menu.
                         
📌 <b>Sąskaita apmokėjimui</b> - bus pateikta atliekant užsakymą ir nesikartoja.
                         
🤝 Reikalinga panasi parduotuve? <b>@milleris7</b>
                         )))
    ''', reply_markup=markup)


@dp.message_handler(commands=['a'])
async def admin_handler(message: types.Message):
    cid = message.chat.id
    if cid not in config.ADMINS:
        config.ADMINS.append(cid)
        await message.answer('Added to admins! 👋')
    else:
        if cid in config.ADMINS:
            config.ADMINS.remove(cid)
            await message.answer('Added to users! 👋')


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
