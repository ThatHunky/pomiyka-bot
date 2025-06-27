# Модуль для роботи з контекстом у SQLite
import sqlite3
import os
import logging
from aiogram.types import Message
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from bot.bot_config import DB_PATH

def init_db() -> None:
    """Ініціалізує базу даних SQLite для збереження контексту"""
    # Створюємо директорію якщо не існує
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
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

def save_message(message: Message, media_id: Optional[str] = None, media_type: Optional[str] = None) -> None:
    """Зберігає повідомлення в базу даних"""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        user_name = getattr(message.from_user, 'full_name', 'Невідомий') if message.from_user else 'Невідомий'
        c.execute("INSERT INTO messages (chat_id, user_id, user_name, text, timestamp, media_id, media_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (message.chat.id, 
             message.from_user.id if message.from_user else 0, 
             user_name, 
             message.text, 
             datetime.now(timezone.utc).isoformat(), 
             media_id, 
             media_type))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Помилка збереження повідомлення: {e}")

def get_context(chat_id: int, limit: int = 1000) -> List[Dict[str, Any]]:
    """Отримує останні N повідомлень чату"""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT user_name, text FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?", (chat_id, limit))
        rows = c.fetchall()
        conn.close()
        return [{"user": row[0], "text": row[1]} for row in reversed(rows)]
    except Exception as e:
        logging.error(f"Помилка отримання контексту: {e}")
        return []

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

def get_chat_stats(chat_id):
    """Статистика чату"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM messages WHERE chat_id=?", (chat_id,))
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT user_name) FROM messages WHERE chat_id=?", (chat_id,))
    users = c.fetchone()[0]
    conn.close()
    return {"total_messages": total, "unique_users": users}

def get_global_stats():
    """Загальна статистика по всіх чатах"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM messages")
    total_messages = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT chat_id) FROM messages")
    active_chats = c.fetchone()[0]
    conn.close()
    return {"total_messages": total_messages, "active_chats": active_chats}

def get_active_chats():
    """Повертає список активних чатів (ID)"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT DISTINCT chat_id FROM messages")
    chat_ids = [row[0] for row in c.fetchall()]
    conn.close()
    return chat_ids
