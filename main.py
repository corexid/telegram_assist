import asyncio
import logging 
import os
from aiogram import Bot, Dispatcher
from aiorgam.types import Message
from aiogram.filters import CommandStart
from dotenv import load_dotenv 

load_dotenv()

BOT_TOKEN = os.dotenv("BOT_TOKEN")
MODERATOR_ID = int(os.dotenv("MODERATOR_ID"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FAQ = {
    "кто мы": "Мы создаем ботов и автомотизацию", 
    "цены": "Стоимость зависит от проекта , напишите нам "
}

def find_faq_answer(text: str):
    text = text.lower()
    for q, a in FAQ.items():
        if q in text:
            return a
        return None
    
    @dp.message(CommandStart())
    async def start(message: Message):
        await message.answer("Приветствуем вас. Задайте ваш вопрос.")
@dp.message()
async def handle_msg(message: Message):
    user_id = message.from_user.id
    text = message.text.lower()

    answer = find_faq_answer(text)

    if answer:
        await message.answer(answer)
    else:
        await message.answer("Передаю менеджеру")
        await bot.send_message(
            MODERATOR_ID,
            f"Клиент:\nID: {user_id} \nСообщение: {message.text}"
        )

asyns def main():
    await dp.start_polling(bot)

    if __name__ == "__main__":
        asyncio.run(main()) 