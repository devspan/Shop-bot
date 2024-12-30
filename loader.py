from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.db.storage import DatabaseManager
from data import config
import sys

if not config.BOT_TOKEN:
    print("No token provided. Please set BOT_TOKEN environment variable")
    sys.exit(1)

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = DatabaseManager('data/database.db')