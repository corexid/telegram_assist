import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def get_ai_response(user_message: str):
    try:
        # Здесь настраивается "личность" бота для бизнеса
        completion = client.chat.completions.create(
            model="llama3-8b-8192", # Быстрая и мощная модель
            messages=[
                {"role": "system", "content": "Ты профессиональный ассистент компании. Отвечай кратко и по делу."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Ошибка ИИ: {e}"