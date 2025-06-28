# Модуль для роботи з контекстом у SQLite
import sqlite3
import json
import logging
import os
from aiogram.types import Message
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union

from bot.bot_config import DB_PATH

def init_db() -> None:
    """Ініціалізує базу даних SQLite для збереження контексту"""
    # Створюємо директорію якщо не існує
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Створюємо таблицю, якщо її немає
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        text TEXT,
        timestamp TEXT
    )''')
    # Перевіряємо схему та додаємо нові стовпці, якщо потрібно
    c.execute("PRAGMA table_info(messages)")
    existing_cols = [row[1] for row in c.fetchall()]
    if 'user_name' not in existing_cols:
        c.execute("ALTER TABLE messages ADD COLUMN user_name TEXT DEFAULT 'Невідомий'")
    if 'media_id' not in existing_cols:
        c.execute("ALTER TABLE messages ADD COLUMN media_id TEXT")
    if 'media_type' not in existing_cols:
        c.execute("ALTER TABLE messages ADD COLUMN media_type TEXT")
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

def get_context(chat_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Отримує останні N повідомлень чату, включаючи імена користувачів."""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Додаємо user_name до запиту
        c.execute("SELECT user_name, text FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT ?", (chat_id, limit))
        rows = c.fetchall()
        conn.close()
        # Повертаємо список словників з іменами користувачів та текстом
        return [{"user_name": row[0], "text": row[1]} for row in reversed(rows)]
    except Exception as e:
        logging.error(f"Помилка отримання контексту: {e}")
        return []

def get_recent_messages(chat_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Отримує останні N повідомлень чату з повною інформацією про користувачів."""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Отримуємо повну інформацію про повідомлення
        c.execute("""SELECT user_name, text, timestamp, user_id, media_type 
                     FROM messages 
                     WHERE chat_id=? 
                     ORDER BY id DESC 
                     LIMIT ?""", (chat_id, limit))
        rows = c.fetchall()
        conn.close()
        
        # Повертаємо список словників з повною інформацією
        messages = []
        for row in reversed(rows):
            messages.append({
                "full_name": row[0] or "Невідомий",
                "username": row[0] or "Невідомий", 
                "text": row[1] or "",
                "timestamp": row[2],
                "user_id": row[3],
                "media_type": row[4],
                "is_bot": False  # За замовчуванням користувачі не боти
            })
        return messages
    except Exception as e:
        logging.error(f"Помилка отримання останніх повідомлень: {e}")
        return []

def add_message_to_context(chat_id: int, user_name: str, text: str, is_bot: bool = False) -> None:
    """Додає повідомлення до контексту."""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""INSERT INTO messages (chat_id, user_name, text, timestamp, user_id) 
                     VALUES (?, ?, ?, ?, ?)""",
                  (chat_id, user_name, text, datetime.now(timezone.utc).isoformat(), 0))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Помилка додавання повідомлення до контексту: {e}")

# Імпорт історії з Telegram JSON

def import_telegram_history(json_path: str, chat_id: int) -> None:
    """Імпортує історію чату з JSON файлу Telegram"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        
        messages: List[Dict[str, Any]] = data.get("messages", [])
        for msg in messages:
            user: str = msg.get("from", "Unknown")
            text_or_parts: Union[str, List[Union[str, Dict[str, str]]]] = msg.get("text", "")
            text: str
            if isinstance(text_or_parts, list):
                # Обробка форматованого тексту
                text_parts: List[Union[str, Dict[str, str]]] = text_or_parts
                text = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in text_parts])
            else:
                text = str(text_or_parts)
            
            timestamp: str = msg.get("date", datetime.now(timezone.utc).isoformat())
            save_message_obj(chat_id, user, text, timestamp)
        logging.info(f"Імпортовано історію для чату {chat_id} з {json_path}")
    except FileNotFoundError:
        logging.error(f"Файл не знайдено: {json_path}")
    except json.JSONDecodeError:
        logging.error(f"Помилка декодування JSON з файлу: {json_path}")
    except Exception as e:
        logging.error(f"Невідома помилка під час імпорту історії: {e}")


def save_message_obj(chat_id: int, user: str, text: str, timestamp: str) -> None:
    """Зберігає одне повідомлення в БД"""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, user_name, text, timestamp) VALUES (?, ?, ?, ?)",
        (chat_id, user, text, timestamp))
    conn.commit()
    conn.close()

def get_chat_stats(chat_id: int) -> Dict[str, int]:
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
