import sqlite3
from datetime import datetime, timezone
from typing import Iterable, Optional

DB_PATH = "users.db"


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db(owner_id: int) -> None:
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_state (
            user_id INTEGER PRIMARY KEY,
            unanswered_count INTEGER DEFAULT 0
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lead_states (
            user_id INTEGER PRIMARY KEY,
            step TEXT,
            name TEXT,
            phone TEXT,
            budget TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            budget TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS faq (
            question TEXT PRIMARY KEY,
            answer TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS moderators (
            user_id INTEGER PRIMARY KEY,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        "INSERT OR IGNORE INTO moderators (user_id) VALUES (?)",
        (owner_id,),
    )

    conn.commit()
    conn.close()


def add_user(user_id: int, username: Optional[str]) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username),
    )
    conn.commit()
    conn.close()


def add_message(user_id: int, role: str, text: str) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (user_id, role, text) VALUES (?, ?, ?)",
        (user_id, role, text),
    )
    conn.commit()
    conn.close()


def get_recent_messages(user_id: int, limit: int) -> list[tuple[str, str]]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT role, text
        FROM messages
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    rows.reverse()
    return rows


def get_users() -> list[int]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_unanswered_count(user_id: int) -> int:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unanswered_count FROM user_state WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return int(row[0]) if row else 0


def set_unanswered_count(user_id: int, count: int) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO user_state (user_id, unanswered_count)
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET unanswered_count = excluded.unanswered_count
        """,
        (user_id, count),
    )
    conn.commit()
    conn.close()


def get_lead_state(user_id: int) -> Optional[dict]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT step, name, phone, budget FROM lead_states WHERE user_id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"step": row[0], "name": row[1], "phone": row[2], "budget": row[3]}


def set_lead_state(user_id: int, step: str, name: str | None, phone: str | None, budget: str | None) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO lead_states (user_id, step, name, phone, budget)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            step = excluded.step,
            name = excluded.name,
            phone = excluded.phone,
            budget = excluded.budget,
            updated_at = CURRENT_TIMESTAMP
        """,
        (user_id, step, name, phone, budget),
    )
    conn.commit()
    conn.close()


def clear_lead_state(user_id: int) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lead_states WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def add_lead(user_id: int, name: str, phone: str, budget: str) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO leads (user_id, name, phone, budget) VALUES (?, ?, ?, ?)",
        (user_id, name, phone, budget),
    )
    conn.commit()
    conn.close()


def add_faq(question: str, answer: str) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO faq (question, answer)
        VALUES (?, ?)
        ON CONFLICT(question) DO UPDATE SET answer = excluded.answer
        """,
        (question.lower().strip(), answer),
    )
    conn.commit()
    conn.close()


def remove_faq(question: str) -> int:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faq WHERE question = ?", (question.lower().strip(),))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def list_faq() -> list[tuple[str, str]]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM faq ORDER BY question")
    rows = cursor.fetchall()
    conn.close()
    return rows


def find_faq(question_text: str) -> Optional[str]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM faq")
    rows = cursor.fetchall()
    conn.close()
    text = question_text.lower()
    for q, a in rows:
        if q in text:
            return a
    return None


def is_moderator(user_id: int) -> bool:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM moderators WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return bool(row)


def add_moderator(user_id: int) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO moderators (user_id) VALUES (?)",
        (user_id,),
    )
    conn.commit()
    conn.close()


def remove_moderator(user_id: int) -> int:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM moderators WHERE user_id = ?", (user_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted


def list_moderators() -> list[int]:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM moderators ORDER BY user_id")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def get_stats() -> dict:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(DISTINCT user_id)
        FROM messages
        WHERE date(created_at) = date('now', 'localtime')
        """
    )
    active_today = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads")
    leads_count = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE date(created_at) = date('now', 'localtime')
        """
    )
    leads_today = cursor.fetchone()[0]

    conn.close()
    return {
        "users": users_count,
        "active_today": active_today,
        "leads_total": leads_count,
        "leads_today": leads_today,
    }
