import asyncio
from aiogram import Bot
import os
from dotenv import load_dotenv

async def test_token(token):
    try:
        bot = Bot(token=token)
        bot_info = await bot.get_me()
        print(f"Successfully connected! Bot name: {bot_info.username}")
        await bot.session.close()
    except Exception as e:
        print(f"Error: {e}")
        print(f"Token being used: {token[:5]}...{token[-5:]}")

if __name__ == "__main__":
    load_dotenv()
    
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("No token found in environment variables!")
        exit(1)
    asyncio.run(test_token(token)) 