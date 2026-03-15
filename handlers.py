import logging
import os
import re
from typing import Optional

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from ai_service import ask_ai
from config import MODERATOR_ID, PORTFOLIO_PDF, RAG_DIR
from database import (
    add_lead,
    add_message,
    add_moderator,
    add_user,
    clear_lead_state,
    get_lead_state,
    get_recent_messages,
    get_stats,
    get_unanswered_count,
    get_users,
    is_moderator,
    list_moderators,
    remove_moderator,
    set_lead_state,
    set_unanswered_count,
)
from rag import get_rag_context, load_kb
from sheets import append_lead

router = Router()

KB_DOCS = load_kb()

LEAD_TRIGGER_WORDS = (
    "заказать",
    "хочу",
    "интересует",
    "нужен",
    "нужна",
    "консультация",
    "связаться",
    "оставить заявку",
    "хочу заказать",
)

HUMAN_WORDS = (
    "живой человек",
    "оператор",
    "менеджер",
    "свяжите",
    "перезвоните",
    "человек",
    "саппорт",
    "поддержка",
)

PHONE_RE = re.compile(r"^\+?\d{10,15}$")


def _is_human_request(text: str) -> bool:
    t = text.lower()
    return any(word in t for word in HUMAN_WORDS)


def _should_start_lead(text: str) -> bool:
    t = text.lower()
    return any(word in t for word in LEAD_TRIGGER_WORDS)


def _format_context_messages(rows: list[tuple[str, str]]) -> list[dict]:
    return [{"role": role, "content": text} for role, text in rows]


async def _send_dialog_to_moderator(message: Message, reason: str) -> None:
    recent = get_recent_messages(message.from_user.id, limit=12)
    lines = [f"{role}: {text}" for role, text in recent]
    payload = "\n".join(lines) if lines else "(нет истории)"
    await message.bot.send_message(
        int(MODERATOR_ID),
        f"Нужна помощь: {reason}\nПользователь: {message.from_user.id}\n\n{payload}",
    )


@router.message(CommandStart())
async def start(message: Message):
    add_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"Привет, {message.from_user.first_name}! "
        "Я ваш AI-ассистент. Задайте вопрос или опишите задачу."
    )


@router.message(Command("help"))
async def help_cmd(message: Message):
    base = [
        "Доступные команды:",
        "/start — начать диалог",
        "/help — помощь",
        "/cancel — отменить сбор данных",
    ]
    if is_moderator(message.from_user.id):
        base.extend(
            [
                "/admin — админ-команды",
            ]
        )
    await message.answer("\n".join(base))


@router.message(Command("admin"))
async def admin_cmd(message: Message):
    if not is_moderator(message.from_user.id):
        return
    await message.answer(
        "Админ-команды:\n"
        "/stats — статистика\n"
        "/broadcast — рассылка\n"
        "/moderator_add — добавить модератора\n"
        "/moderator_del — удалить модератора\n"
        "/moderators — список модераторов\n"
        "/kb_reload — обновить базу знаний\n"
        "/kb_add — добавить документ в базу знаний"
    )



@router.message(Command("stats"))
async def stats_cmd(message: Message):
    if not is_moderator(message.from_user.id):
        return
        return
    stats = get_stats()
    await message.answer(
        "Статистика:\n"
        f"Пользователи: {stats['users']}\n"
        f"Активные сегодня: {stats['active_today']}\n"
        f"Лиды всего: {stats['leads_total']}\n"
        f"Лиды сегодня: {stats['leads_today']}"
    )


@router.message(Command("broadcast"))
async def broadcast_cmd(message: Message):
    if not is_moderator(message.from_user.id):
        return
        return

    text = message.text or message.caption or ""
    payload = text.replace("/broadcast", "", 1).strip()
    users = get_users()
    sent = 0

    if message.photo:
        caption = message.caption or ""
        caption_payload = caption.replace("/broadcast", "", 1).strip()
        if not caption_payload:
            await message.answer("Добавьте текст после /broadcast в подписи фото.")
            return
        photo = message.photo[-1].file_id
        for uid in users:
            try:
                await message.bot.send_photo(uid, photo, caption=caption_payload)
                sent += 1
            except Exception:
                continue
        await message.answer(f"Рассылка завершена. Отправлено: {sent}")
        return

    if not payload:
        await message.answer("Использование: /broadcast текст рассылки")
        return

    for uid in users:
        try:
            await message.bot.send_message(uid, payload)
            sent += 1
        except Exception:
            continue
    await message.answer(f"Рассылка завершена. Отправлено: {sent}")



@router.message(Command("moderator_add"))
async def moderator_add_cmd(message: Message):
    if message.from_user.id != int(MODERATOR_ID):
        return
        return
    text = (message.text or "").replace("/moderator_add", "", 1).strip()
    if not text.isdigit():
        await message.answer("Формат: /moderator_add 123456789")
        return
    add_moderator(int(text))
    await message.answer("Модератор добавлен.")


@router.message(Command("moderator_del"))
async def moderator_del_cmd(message: Message):
    if message.from_user.id != int(MODERATOR_ID):
        return
        return
    text = (message.text or "").replace("/moderator_del", "", 1).strip()
    if not text.isdigit():
        await message.answer("Формат: /moderator_del 123456789")
        return
    deleted = remove_moderator(int(text))
    if deleted:
        await message.answer("Модератор удален.")
    else:
        await message.answer("Модератор не найден.")


@router.message(Command("moderators"))
async def moderators_cmd(message: Message):
    if not is_moderator(message.from_user.id):
        return
        return
    mods = list_moderators()
    await message.answer("Модераторы:\n" + "\n".join(str(m) for m in mods))


@router.message(Command("kb_reload"))
async def kb_reload_cmd(message: Message):
    if not is_moderator(message.from_user.id):
        return
        return
    global KB_DOCS
    KB_DOCS = load_kb()
    await message.answer(f"База знаний обновлена. Файлов: {len(KB_DOCS)}")


@router.message(Command("kb_add"))
async def kb_add_cmd(message: Message):
    if not is_moderator(message.from_user.id):
        return
        return

    global KB_DOCS
    text = (message.text or "").replace("/kb_add", "", 1).strip()

    if message.document:
        doc = message.document
        filename = doc.file_name or f"doc_{doc.file_id}.bin"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".pdf", ".json"]:
            await message.answer("Поддерживаются только PDF или JSON файлы.")
            return
        os.makedirs(RAG_DIR, exist_ok=True)
        save_path = os.path.join(RAG_DIR, filename)
        file = await message.bot.get_file(doc.file_id)
        await message.bot.download_file(file.file_path, destination=save_path)
        KB_DOCS = load_kb()
        await message.answer(f"Файл добавлен. База знаний обновлена. Файлов: {len(KB_DOCS)}")
        return

    if text:
        os.makedirs(RAG_DIR, exist_ok=True)
        filename = f"kb_note_{message.message_id}.json"
        save_path = os.path.join(RAG_DIR, filename)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)
        KB_DOCS = load_kb()
        await message.answer(f"Текст добавлен. База знаний обновлена. Файлов: {len(KB_DOCS)}")
        return

    await message.answer(
        "Использование:\n"
        "1) /kb_add текст\n"
        "2) /kb_add и приложить PDF/JSON файлом"
    )


@router.message(Command("cancel"))
async def cancel_cmd(message: Message):
    clear_lead_state(message.from_user.id)
    await message.answer("Ок, отменил сбор данных. Чем могу помочь?")


@router.message(F.caption.startswith("/broadcast"))
async def broadcast_photo_cmd(message: Message):
    await broadcast_cmd(message)


@router.message()
async def handle_msg(message: Message):
    user = message.from_user
    if user is None:
        return

    add_user(user.id, user.username)

    text = message.text or message.caption
    if text is None:
        await message.answer("Я понимаю только текстовые сообщения. Напишите, пожалуйста, текст.")
        return

    text = text.strip()
    if not text:
        await message.answer("Пожалуйста, отправьте текст.")
        return

    add_message(user.id, "user", text)

    lead_state = get_lead_state(user.id)
    if lead_state:
        await _handle_lead_flow(message, text, lead_state)
        return

    if _is_human_request(text):
        await message.answer("Подключаю специалиста. Пожалуйста, ожидайте.")
        await _send_dialog_to_moderator(message, "Запрос живого человека")
        return

    if _should_start_lead(text):
        set_lead_state(user.id, "name", None, None, None)
        await message.answer("Отлично! Как вас зовут?")
        return

    rag_context = get_rag_context(text, KB_DOCS)
    context_rows = get_recent_messages(user.id, limit=12)
    context_messages = _format_context_messages(context_rows)

    ai_answer = await ask_ai(
        user_text=text,
        context_messages=context_messages,
        rag_context=rag_context,
        user_id=user.id,
    )

    if ai_answer:
        set_unanswered_count(user.id, 0)
        await message.answer(ai_answer)
        add_message(user.id, "assistant", ai_answer)

        if _should_send_portfolio(text, context_rows):
            await _send_portfolio_if_exists(message)
        return

    if user.id == 1669935123:
        set_unanswered_count(user.id, 0)
        reply = (
            "Солнышко, сейчас не смогла быстро ответить. "
            "Скажи, пожалуйста, чуть точнее, что именно ты хочешь узнать?"
        )
        await message.answer(reply)
        add_message(user.id, "assistant", reply)
        return

    unanswered = get_unanswered_count(user.id) + 1
    set_unanswered_count(user.id, unanswered)
    if unanswered >= 2:
        await message.answer("Секундочку, передам ваш вопрос специалисту...")
        await _send_dialog_to_moderator(message, "ИИ не смог ответить 2 раза подряд")
    else:
        await message.answer(
            "Не нашел точный ответ. Уточните, пожалуйста, что именно вас интересует?"
        )


def _should_send_portfolio(text: str, context_rows: list[tuple[str, str]]) -> bool:
    t = text.lower()
    if "пришл" in t or "да" == t or "да!" == t:
        for role, msg in context_rows[-6:]:
            if role == "assistant" and ("примеры" in msg.lower() or "портфолио" in msg.lower()):
                return True
    return False


async def _send_portfolio_if_exists(message: Message) -> None:
    if os.path.exists(PORTFOLIO_PDF):
        await message.answer_document(types.FSInputFile(PORTFOLIO_PDF))
        await message.answer("Готовы обсудить детали и рассчитать стоимость?")
    else:
        await message.answer(
            "Портфолио пока не загружено. "
            "Добавьте файл в папку и я сразу начну отправлять его."
        )


async def _handle_lead_flow(message: Message, text: str, state: dict) -> None:
    step = state["step"]
    user_id = message.from_user.id

    if step == "name":
        name = text
        set_lead_state(user_id, "phone", name, None, None)
        await message.answer("Спасибо! Укажите телефон в формате +375XXXXXXXXX")
        return

    if step == "phone":
        if not PHONE_RE.match(text):
            await message.answer("Проверьте номер. Формат: +375XXXXXXXXX")
            return
        set_lead_state(user_id, "budget", state["name"], text, None)
        await message.answer("Какой у вас бюджет (или диапазон)?")
        return

    if step == "budget":
        name = state["name"] or "Клиент"
        phone = state["phone"] or ""
        budget = text
        add_lead(user_id, name, phone, budget)
        append_lead(name, phone, budget, user_id)
        clear_lead_state(user_id)
        await message.answer("Спасибо! Передал данные менеджеру. Свяжемся с вами.")
        await _send_dialog_to_moderator(message, "Новый лид")
        return
