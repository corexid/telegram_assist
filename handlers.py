import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from annotated_types import Not
from ai_service import get_ai_response
from database import add_user
from main import MODERATOR_ID, ask_ai, find_faq_answer

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    # Сохраняем пользователя в базу данных
    add_user(message.from_user.id, message.from_user.username)

    await message.answer(
        f"Привет, {message.from_user.first_name}! Я твой ИИ-ассистент. "
        "Задай мне любой вопрос, и я постараюсь помочь."
    )


@router.message()
async def handle_msg(message: Message):
    user_id = message.from_user.id
    text = message.text.lower()

    # 1. Сначала ищем в быстром FAQ
    answer = find_faq_answer(text)
    if answer:
        await message.answer(answer)
        return

    # 2. Если в FAQ нет, идем к нейросети
    await Not.send_chat_action(message.chat.id, "typing")

    # Пытаемся получить ответ от ИИ
    ai_answer = await ask_ai(message.text)

    # ВАЖНО: Проверяем, что ИИ хоть что-то вернул
    if ai_answer and len(ai_answer.strip()) > 0:
        await message.answer(ai_answer)
    else:
        # Только если ИИ реально выдал None или пустую строку, идем к менеджеру
        logging.warning(
            f"ИИ не смог ответить пользователю {user_id}. Текст: {message.text}"
        )
        await message.answer("Секундочку, передаю ваш вопрос специалисту...")
        await Not.send_message(
            MODERATOR_ID, f" ИИ не справился!\nID: {user_id}\nТекст: {message.text}"
        )
