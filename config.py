import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MODERATOR_ID = os.getenv("MODERATOR_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

RAG_DIR = os.getenv("RAG_DIR", "datarag")
PORTFOLIO_PDF = os.getenv("PORTFOLIO_PDF", os.path.join(RAG_DIR, "portfolio.pdf"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")
if not MODERATOR_ID:
    raise RuntimeError("MODERATOR_ID is not set")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set")
