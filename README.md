# Telegram Assist

Telegram-бот на `aiogram` с быстрым FAQ и ответами от Groq LLM. Если ИИ не
возвращает ответ, бот уведомляет модератора.

## Возможности
- FAQ-ответы по ключевым вопросам + управление FAQ через команды
- Генерация ответов через Groq (с ограничением по времени)
- Простая RAG-база знаний (PDF/JSON из папки `datarag`)
- Контекстная память последних сообщений пользователя
- Лид-анкета (имя, телефон, бюджет) и отправка в Google Sheets
- Эскалация к модератору при запросе живого человека или при 2 подряд неудачных ответах
- Команды `/start`, `/help`, `/faq`, `/stats`, `/broadcast`, `/kb_reload`

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
   # Опционально: Google Sheets
   GOOGLE_SHEETS_ID=spreadsheet_id
   GOOGLE_CREDENTIALS_JSON=C:\path\to\service_account.json
   # или JSON строкой:
   # GOOGLE_CREDENTIALS={"type":"service_account",...}
   # RAG
   RAG_DIR=datarag
   PORTFOLIO_PDF=datarag\portfolio.pdf
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
- `rag.py` — загрузка PDF/JSON и поиск контекста
- `sheets.py` — отправка лидов в Google Sheets

## RAG-файлы
Положите файлы `*.pdf` и `*.json` в папку `datarag`.
Портфолио отправляется из файла `datarag/portfolio.pdf`.

## Команды модератора
- `/stats` — статистика
- `/broadcast текст` — рассылка
- `/faq_add вопрос | ответ`
- `/faq_del вопрос`
- `/moderator_add 123456789`
- `/moderator_del 123456789`
- `/moderators`
- `/kb_reload`
