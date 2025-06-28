# Спрощений асинхронний модуль для роботи з контекстом (без connection pool)
import aiosqlite
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# Шлях до бази даних
DB_PATH = os.path.join("data", "context_async.db")

# Глобальне з'єднання
_global_connection: Optional[aiosqlite.Connection] = None

async def get_connection() -> aiosqlite.Connection:
    """Отримує глобальне з'єднання з БД"""
    global _global_connection
    
    if _global_connection is None:
        # Створюємо директорію якщо не існує
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        
        _global_connection = await aiosqlite.connect(DB_PATH)
        # Налаштування для кращої продуктивності
        await _global_connection.execute("PRAGMA journal_mode=WAL")
        await _global_connection.execute("PRAGMA synchronous=NORMAL")
        await _global_connection.execute("PRAGMA cache_size=10000")
        await _global_connection.execute("PRAGMA temp_store=memory")
        
        logger.info("Database connection established")
    
    return _global_connection

async def close_connection():
    """Закриває глобальне з'єднання"""
    global _global_connection
    
    if _global_connection:
        await _global_connection.close()
        _global_connection = None
        logger.info("Database connection closed")

async def init_database():
    """Ініціалізація бази даних з покращеними індексами"""
    conn = await get_connection()
    
    try:
        # Створення таблиць
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER,
                username TEXT,
                full_name TEXT,
                message_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                message_type TEXT DEFAULT 'text',
                media_description TEXT,
                reply_to_message_id INTEGER
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                context_data TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                context_type TEXT DEFAULT 'conversation'
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Покращені індекси для продуктивності
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_messages_chat_time ON messages(chat_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_chat_user ON messages(chat_id, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_context_chat ON context(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_context_updated ON context(last_updated)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_chat_type ON analytics(chat_id, event_type)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_time ON analytics(timestamp)",
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        await conn.commit()
        logger.info("Database initialized with optimized indexes")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def add_message_to_context(chat_id: int, user_id: int, username: str, 
                                full_name: str, message_text: str, 
                                message_type: str = "text", 
                                media_description: Optional[str] = None,
                                reply_to_message_id: Optional[int] = None) -> None:
    """Додає повідомлення до контексту чату"""
    conn = await get_connection()
    
    try:
        await conn.execute('''
            INSERT INTO messages 
            (chat_id, user_id, username, full_name, message_text, message_type, media_description, reply_to_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (chat_id, user_id, username, full_name, message_text, message_type, media_description, reply_to_message_id))
        
        await conn.commit()
        
    except Exception as e:
        logger.error(f"Error adding message to context: {e}")
        raise

async def get_recent_messages(chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Отримує останні повідомлення з чату з покращеною продуктивністю"""
    conn = await get_connection()
    
    try:
        # Оптимізований запит з використанням індексу
        async with conn.execute('''
            SELECT user_id, username, full_name, message_text, timestamp, 
                   message_type, media_description, reply_to_message_id
            FROM messages 
            WHERE chat_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (chat_id, limit)) as cursor:
            
            rows = await cursor.fetchall()
            
        messages = []
        for row in rows:
            messages.append({
                'user_id': row[0],
                'username': row[1],
                'full_name': row[2],
                'message_text': row[3],
                'timestamp': row[4],
                'message_type': row[5],
                'media_description': row[6],
                'reply_to_message_id': row[7]
            })
        
        # Повертаємо в хронологічному порядку
        return list(reversed(messages))
        
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        return []

async def get_context_summary(chat_id: int, hours: int = 24) -> str:
    """Генерує короткий опис контексту за останні години"""
    since = datetime.now() - timedelta(hours=hours)
    messages = await get_recent_messages(chat_id, limit=100)
    
    context_lines = []
    for msg in messages:
        if datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00')) > since:
            username = msg['username'] or msg['full_name'] or 'Unknown'
            if msg['message_type'] == 'text':
                context_lines.append(f"{username}: {msg['message_text']}")
            elif msg['media_description']:
                context_lines.append(f"{username}: [медіа: {msg['media_description']}]")
            else:
                context_lines.append(f"{username}: [медіа файл]")
    
    return "\n".join(context_lines)

async def get_database_stats() -> Dict[str, Any]:
    """Отримує статистику бази даних"""
    conn = await get_connection()
    
    try:
        stats = {}
        
        # Загальна кількість повідомлень
        async with conn.execute('SELECT COUNT(*) FROM messages') as cursor:
            result = await cursor.fetchone()
            stats['total_messages'] = result[0] if result else 0
        
        # Повідомлення за останні 24 години
        since = datetime.now() - timedelta(hours=24)
        async with conn.execute(
            'SELECT COUNT(*) FROM messages WHERE timestamp > ?', 
            (since.isoformat(),)
        ) as cursor:
            result = await cursor.fetchone()
            stats['recent_messages'] = result[0] if result else 0
        
        # Кількість унікальних чатів
        async with conn.execute('SELECT COUNT(DISTINCT chat_id) FROM messages') as cursor:
            result = await cursor.fetchone()
            stats['unique_chats'] = result[0] if result else 0
        
        # Кількість унікальних користувачів
        async with conn.execute('SELECT COUNT(DISTINCT user_id) FROM messages') as cursor:
            result = await cursor.fetchone()
            stats['unique_users'] = result[0] if result else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {}

async def cleanup_old_messages(days: int = 30):
    """Видаляє старі повідомлення"""
    conn = await get_connection()
    
    try:
        cutoff = datetime.now() - timedelta(days=days)
        
        async with conn.execute(
            'DELETE FROM messages WHERE timestamp < ?', 
            (cutoff.isoformat(),)
        ) as cursor:
            deleted_count = cursor.rowcount
        
        await conn.commit()
        logger.info(f"Deleted {deleted_count} old messages")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old messages: {e}")
        return 0

async def log_analytics_event(chat_id: int, event_type: str, event_data: Optional[Dict[str, Any]] = None):
    """Логує аналітичну подію"""
    conn = await get_connection()
    
    try:
        event_data_json = json.dumps(event_data) if event_data else None
        
        await conn.execute('''
            INSERT INTO analytics (chat_id, event_type, event_data)
            VALUES (?, ?, ?)
        ''', (chat_id, event_type, event_data_json))
        
        await conn.commit()
        
    except Exception as e:
        logger.error(f"Error logging analytics event: {e}")

async def get_analytics_summary(chat_id: int, hours: int = 24) -> Dict[str, Any]:
    """Отримує аналітичну статистику"""
    conn = await get_connection()
    
    try:
        since = datetime.now() - timedelta(hours=hours)
        
        async with conn.execute('''
            SELECT event_type, COUNT(*) 
            FROM analytics 
            WHERE chat_id = ? AND timestamp > ?
            GROUP BY event_type
        ''', (chat_id, since.isoformat())) as cursor:
            
            rows = await cursor.fetchall()
            
        return {row[0]: row[1] for row in rows}
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        return {}

# Зворотна сумісність з context_sqlite.py
class AsyncContextManager:
    """Менеджер асинхронного контексту для зворотної сумісності"""
    
    def __init__(self):
        self.db_path = DB_PATH
    
    async def initialize(self):
        """Ініціалізація"""
        await init_database()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Статистика"""
        return await get_database_stats()
    
    async def save_message(self, message: Any, media_id: Optional[str] = None, media_type: Optional[str] = None):
        """Збереження повідомлення"""
        
        if hasattr(message, 'from_user') and message.from_user:
            user_id = message.from_user.id
            username = message.from_user.username or ""
            full_name = message.from_user.full_name or ""
        else:
            user_id = 0
            username = ""
            full_name = ""
        
        chat_id = message.chat.id if hasattr(message, 'chat') else 0
        message_text = message.text if hasattr(message, 'text') else ""
        message_type = media_type or "text"
        
        await add_message_to_context(
            chat_id=chat_id,
            user_id=user_id,
            username=username,
            full_name=full_name,
            message_text=message_text,
            message_type=message_type,
            media_description=media_id
        )
    
    async def get_recent_context(self, chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Отримання останнього контексту"""
        return await get_recent_messages(chat_id, limit)

# Псевдоніми для зворотної сумісності
ContextManager = AsyncContextManager  # Для сумісності
context_manager = None  # Глобальний менеджер

async def get_context_manager() -> AsyncContextManager:
    """Отримує глобальний менеджер контексту"""
    global context_manager
    if context_manager is None:
        context_manager = AsyncContextManager()
        await context_manager.initialize()
    return context_manager
