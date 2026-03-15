import sqlite3

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Создаем таблицу, если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Добавляем пользователя (если его нет, игнорируем)
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                   (user_id, username))
    conn.commit()
    conn.close()