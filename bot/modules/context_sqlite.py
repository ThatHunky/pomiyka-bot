# Модуль для роботи з контекстом у SQLite
import sqlite3
from aiogram.types import Message
from datetime import datetime
import os

DB_PATH = "bot/context.db"

# Ініціалізація бази

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        user_name TEXT,
        text TEXT,
        timestamp TEXT,
        media_id TEXT,
        media_type TEXT
    )''')
    conn.commit()
    conn.close()

# Зберегти повідомлення

def save_message(message: Message, media_id=None, media_type=None):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, user_id, user_name, text, timestamp, media_id, media_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (message.chat.id, message.from_user.id, message.from_user.full_name, message.text, datetime.utcnow().isoformat(), media_id, media_type))
    conn.commit()
    conn.close()

# Отримати останні N повідомлень чату

def get_context(chat_id, limit=1000):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_name, text FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?", (chat_id, limit))
    rows = c.fetchall()
    conn.close()
    return [{"user": row[0], "text": row[1]} for row in reversed(rows)]

# Імпорт історії з Telegram JSON

def import_telegram_history(json_path, chat_id):
    import json
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for msg in data.get("messages", []):
        user = msg.get("from", "Unknown")
        text = msg.get("text", "")
        if isinstance(text, list):
            text = " ".join([t if isinstance(t, str) else t.get("text", "") for t in text])
        timestamp = msg.get("date", datetime.utcnow().isoformat())
        save_message_obj(chat_id, user, text, timestamp)

def save_message_obj(chat_id, user, text, timestamp):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, user_name, text, timestamp) VALUES (?, ?, ?, ?)",
        (chat_id, user, text, timestamp))
    conn.commit()
    conn.close()
