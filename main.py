import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from groq import Groq

# Импортируем функции базы данных из твоего файла database.py
from database import init_db, add_user

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MODERATOR_ID = int(os.getenv("MODERATOR_ID"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Инициализируем клиента Groq
client = Groq(api_key=GROQ_API_KEY)

# Логирование обязательно — оно покажет ошибки в консоли, если они будут
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

FAQ = {
    "кто мы": "Мы создаем Telegram ботов и автоматизацию бизнеса.",
    "цены": "Стоимость зависит от проекта. Опишите задачу.",
}


def find_faq_answer(text: str):
    text = text.lower()
    for q, a in FAQ.items():
        if q in text:
            return a
    return None


async def ask_ai(user_text: str):
    try:
        # Важно: используем асинхронный вызов, если возможно,
        # но для начала оставим так, как в документации Groq
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Мощная модель для сложных вопросов
            messages=[
                {
                    "role": "system",
                    "content": "Ты — ведущий менеджер IT-студии. Твоя задача — отвечать на любые вопросы клиента вежливо и экспертно. Если клиент спрашивает что-то странное, всё равно попытайся ответить в контексте разработки ботов.Если зайдет человек с user_id=1669935123? то просто скажи что она обезьяна такая вот крутая , ну можешь от себя чето добавить потому что это моя девушка, только я тебе этого не говорил, а то она обидится. Если человек будет задавать странные вопросы, то просто отвечай ему все равно также как нужно в общении с клиентами, ну или что-то в этом роде, но не груби, ну ты понял да?",
                },
                {"role": "user", "content": user_text},
            ],
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка Groq: {e}")
        return None


@dp.message(CommandStart())
async def start(message: Message):
    # Сохраняем пользователя в базу данных
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Добро пожаловать, {message.from_user.first_name}! Чем могу помочь?"
    )


@dp.message()
async def handle_msg(message: Message):
    user_id = message.from_user.id
    text = message.text.lower()

    answer = find_faq_answer(text)
    if answer:
        await message.answer(answer)
        return

    await bot.send_chat_action(message.chat.id, "typing")
    ai_answer = await ask_ai(message.text)

    if ai_answer:
        await message.answer(ai_answer)
    else:
        await message.answer("Передаю ваш вопрос специалисту...")
        await bot.send_message(
            MODERATOR_ID, f" Нужна помощь!\nID: {user_id}\nТекст: {message.text}"
        )


async def main():
    # Инициализируем базу данных перед запуском бота
    init_db()

    print("Бот успешно запущен!")
    # Удаляем старые сообщения, чтобы бот не отвечал на них при включении
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


# ЭТОТ БЛОК ДОЛЖЕН БЫТЬ БЕЗ ОТСТУПОВ (В САМОМ КРАЮ)
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
