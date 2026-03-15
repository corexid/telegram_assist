import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from database import init_db
from handlers import router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MODERATOR_ID = os.getenv("MODERATOR_ID")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")
if not MODERATOR_ID:
    raise RuntimeError("MODERATOR_ID is not set")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


async def main():
    init_db()
    print("Бот успешно запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
