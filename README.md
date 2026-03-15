# Telegram Assist

Telegram-бот на `aiogram` с быстрым FAQ и ответами от Groq LLM. Если ИИ не
возвращает ответ, бот уведомляет модератора.

## Возможности
- FAQ-ответы по ключевым вопросам
- Генерация ответов через Groq
- Логирование пользователей в SQLite
- Эскалация к модератору при отсутствии ответа
- Команды `/start`, `/help`, `/faq`

## Запуск
1. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Создать `.env`:
   ```env
   BOT_TOKEN=ваш_токен_бота
   MODERATOR_ID=123456789
   GROQ_API_KEY=ваш_api_key
   ```
3. Запустить:
   ```bash
   python main.py
   ```

## Структура
- `main.py` — запуск бота и подключение роутеров
- `handlers.py` — обработчики сообщений и FAQ
- `ai_service.py` — запросы к Groq
- `database.py` — работа с SQLite
