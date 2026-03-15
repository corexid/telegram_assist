import json
import logging
import os
import re
from typing import Iterable

from config import RAG_DIR

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional runtime dependency
    PdfReader = None


def _normalize(text: str) -> list[str]:
    return re.findall(r"[a-zа-я0-9]+", text.lower())


def _score(query_tokens: list[str], doc_tokens: list[str]) -> int:
    if not query_tokens or not doc_tokens:
        return 0
    doc_set = set(doc_tokens)
    return sum(1 for t in query_tokens if t in doc_set)


def _read_pdf(path: str) -> str:
    if PdfReader is None:
        logging.warning("pypdf is not available, skipping PDF: %s", path)
        return ""
    try:
        reader = PdfReader(path)
        chunks = []
        for page in reader.pages:
            try:
                chunks.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(chunks)
    except Exception as exc:
        logging.warning("Failed to read PDF %s: %s", path, exc)
        return ""


def _read_json(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return json.dumps(data, ensure_ascii=False, indent=2)


def load_kb() -> list[dict]:
    os.makedirs(RAG_DIR, exist_ok=True)
    docs: list[dict] = []
    for name in os.listdir(RAG_DIR):
        path = os.path.join(RAG_DIR, name)
        if not os.path.isfile(path):
            continue
        if name.lower().endswith(".pdf"):
            text = _read_pdf(path)
        elif name.lower().endswith(".json"):
            text = _read_json(path)
        else:
            continue
        if text.strip():
            docs.append({"source": name, "text": text})
    logging.info("RAG loaded docs=%s from %s", len(docs), RAG_DIR)
    return docs


def get_rag_context(query: str, docs: list[dict], limit: int = 3, max_chars: int = 1200) -> str:
    if not docs:
        return ""
    q_tokens = _normalize(query)
    scored = []
    for doc in docs:
        d_tokens = _normalize(doc["text"])
        score = _score(q_tokens, d_tokens)
        if score > 0:
            scored.append((score, doc))
    if not scored:
        return ""
    scored.sort(key=lambda x: x[0], reverse=True)
    parts = []
    for _, doc in scored[:limit]:
        snippet = doc["text"][:max_chars]
        parts.append(f"[{doc['source']}]\n{snippet}")
    return "\n\n".join(parts)
