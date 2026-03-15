import logging
import os
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from ai_service import ask_ai
from database import add_user

load_dotenv()

MODERATOR_ID = os.getenv("MODERATOR_ID")
if not MODERATOR_ID:
    raise RuntimeError("MODERATOR_ID is not set")
MODERATOR_ID = int(MODERATOR_ID)

router = Router()

FAQ = {
    "кто мы": "Мы создаем Telegram-ботов и автоматизацию бизнеса.",
    "цены": "Стоимость зависит от проекта. Опишите задачу.",
}


def find_faq_answer(text: str) -> Optional[str]:
    text = text.lower()
    for question, answer in FAQ.items():
        if question in text:
            return answer
    return None


@router.message(CommandStart())
async def start(message: Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Привет, {message.from_user.first_name}! "
        "Я твой ИИ-ассистент. Задай мне любой вопрос, и я постараюсь помочь."
    )


@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "Доступные команды:\n"
        "/start — начать диалог\n"
        "/help — помощь\n"
        "/faq — быстрые ответы\n"
        "\n"
        "Также можно просто написать вопрос сообщением."
    )


@router.message(Command("faq"))
async def faq_cmd(message: Message):
    items = [f"• {q}" for q in FAQ.keys()]
    await message.answer(
        "Частые вопросы:\n" + "\n".join(items) + "\n\nПросто напиши вопрос."
    )


@router.message()
async def handle_msg(message: Message):
    user_id = message.from_user.id
    text = message.text or ""

    answer = find_faq_answer(text)
    if answer:
        await message.answer(answer)
        return

    await message.bot.send_chat_action(message.chat.id, "typing")
    ai_answer = await ask_ai(text)

    if ai_answer and ai_answer.strip():
        await message.answer(ai_answer)
        return

    logging.warning(
        "AI did not return an answer for user_id=%s. Text=%s", user_id, text
    )
    await message.answer("Секундочку, передам ваш вопрос специалисту...")
    await message.bot.send_message(
        MODERATOR_ID, f"Нужна помощь!\nID: {user_id}\nТекст: {text}"
    )
