import logging
import os
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = (
    "Ты — ведущий менеджер IT-студии. Твоя задача — отвечать на любые вопросы "
    "клиента вежливо и экспертно. Если клиент спрашивает что-то странное, "
    "все равно постарайся ответить в контексте разработки ботов. "
    "Если зайдет человек с user_id=1669935123, то просто скажи, что она "
    "обезьяна такая вот крутая, можешь от себя что-то добавить, потому что "
    "это моя девушка, только я тебе этого не говорил, а то она обидится. "
    "Если человек будет задавать странные вопросы, то просто отвечай ему "
    "все равно так, как нужно в общении с клиентами, но не груби."
)


async def ask_ai(user_text: str) -> Optional[str]:
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
        )
        return completion.choices[0].message.content
    except Exception as exc:
        logging.error("Groq error: %s", exc)
        return None
