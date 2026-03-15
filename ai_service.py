import asyncio
import logging
import time
from typing import Optional

from groq import Groq

from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

BASE_SYSTEM_PROMPT = (
    "Ты — ведущий менеджер IT-студии. Твоя задача — отвечать на вопросы клиента "
    "в деловом стиле, экспертно и по делу. Используй отраслевую терминологию. "
    "Всегда заверши ответ призывом к действию (CTA), например: "
    "'Готовы обсудить детали и рассчитать стоимость?' "
    "Если вопрос не по теме — вежливо верни к услугам компании. "
    "Не выдумывай факты: если данных нет в материалах, скажи, что нужно уточнить у менеджера."
)

COMPANY_PROFILE = (
    "Профиль компании (базовый, без деталей): мы IT-студия, занимаемся разработкой "
    "Telegram-ботов, сайтов и автоматизацией бизнес-процессов. Делаем проекты под ключ, "
    "включая аналитику, разработку, тестирование и поддержку. Стоимость и сроки "
    "зависят от задачи и обсуждаются после брифа."
)

GIRLFRIEND_PROMPT = (
    "Отвечай в теплой, ласковой и игривой манере, как близкому человеку. "
    "Используй нежные обращения вроде 'солнышко', 'любимая', 'котик'. "
    "Не используй оскорбления или грубость. "
    "Сохраняй деловой контекст, если вопрос про услуги."
)

HARD_TIMEOUT_SECONDS = 3


def _build_messages(
    user_text: str,
    context_messages: list[dict],
    rag_context: str | None,
    user_id: int | None,
) -> list[dict]:
    system_parts = [BASE_SYSTEM_PROMPT]
    system_parts.append(COMPANY_PROFILE)
    if user_id == 1669935123:
        system_parts.append(GIRLFRIEND_PROMPT)
    if rag_context:
        system_parts.append(
            "Ниже фактические материалы компании. Используй их строго для ответа:\n"
            f"{rag_context}"
        )

    messages = [{"role": "system", "content": "\n\n".join(system_parts)}]
    messages.extend(context_messages)
    messages.append({"role": "user", "content": user_text})
    return messages


def _sync_call(messages: list[dict]) -> str:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
    )
    return completion.choices[0].message.content


async def ask_ai(
    user_text: str,
    context_messages: list[dict],
    rag_context: Optional[str],
    user_id: Optional[int],
) -> Optional[str]:
    messages = _build_messages(user_text, context_messages, rag_context, user_id)
    start = time.monotonic()
    try:
        logging.info("Groq request user_id=%s text=%s", user_id, user_text)
        if rag_context:
            logging.info("Groq RAG context chars=%s", len(rag_context))
        response = await asyncio.wait_for(
            asyncio.to_thread(_sync_call, messages),
            timeout=HARD_TIMEOUT_SECONDS,
        )
        elapsed = time.monotonic() - start
        logging.info("Groq OK in %.2fs, prompt_chars=%s", elapsed, len(user_text))
        return response
    except TimeoutError:
        logging.warning("Groq timeout after %ss", HARD_TIMEOUT_SECONDS)
        return None
    except Exception as exc:
        logging.error("Groq error: %s", exc)
        return None
