# Асинхронний модуль для роботи з контекстом (замінює context_sqlite.py)
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

# Connection pool для оптимізації
_connection_pool: Optional[aiosqlite.Connection] = None
_pool_lock = None

class DatabaseConnectionPool:
    """Простий connection pool для aiosqlite"""
    
    def __init__(self, db_path: str, max_connections: int = 5):
        self.db_path = db_path
        self.max_connections = max_connections
        self._connections: List[aiosqlite.Connection] = []
        self._available: List[aiosqlite.Connection] = []
        self._lock = None
        self._initialized = False

    def _ensure_lock(self):
        """Забезпечує, що lock створений в правильному event loop"""
        if self._lock is None:
            self._lock = asyncio.Lock()

    async def initialize(self):
        """Ініціалізація пулу з'єднань"""
        if self._initialized:
            return
            
        self._ensure_lock()
        async with self._lock:
            if self._initialized:
                return
                
            # Створюємо директорію якщо не існує
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Створюємо з'єднання
            for _ in range(self.max_connections):
                conn = await aiosqlite.connect(self.db_path)
                await conn.execute("PRAGMA journal_mode=WAL")  # Покращена продуктивність
                await conn.execute("PRAGMA synchronous=NORMAL")
                await conn.execute("PRAGMA cache_size=10000")
                await conn.execute("PRAGMA temp_store=memory")
                self._connections.append(conn)
                self._available.append(conn)
            
            self._initialized = True
            logger.info(f"Database connection pool initialized with {self.max_connections} connections")

    async def get_connection(self) -> aiosqlite.Connection:
        """Отримати з'єднання з пулу"""
        await self.initialize()
        
        self._ensure_lock()
        async with self._lock:
            if self._available:
                return self._available.pop()
            else:
                # Якщо немає доступних з'єднань, створюємо тимчасове
                logger.warning("No available connections in pool, creating temporary connection")
                conn = await aiosqlite.connect(self.db_path)
                await conn.execute("PRAGMA journal_mode=WAL")
                return conn

    async def return_connection(self, conn: aiosqlite.Connection):
        """Повернути з'єднання до пулу"""
        self._ensure_lock()
        async with self._lock:
            if conn in self._connections:
                self._available.append(conn)
            else:
                # Тимчасове з'єднання, закриваємо
                await conn.close()

    async def close_all(self):
        """Закрити всі з'єднання"""
        self._ensure_lock()
        async with self._lock:
            for conn in self._connections:
                await conn.close()
            self._connections.clear()
            self._available.clear()
            self._initialized = False

# Глобальний пул з'єднань
_db_pool = DatabaseConnectionPool(DB_PATH)

async def init_database():
    """Ініціалізація бази даних з покращеними індексами"""
    await _db_pool.initialize()
    conn = await _db_pool.get_connection()
    
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
        
    finally:
        await _db_pool.return_connection(conn)

async def add_message_to_context(chat_id: int, user_id: int, username: str, 
                                full_name: str, message_text: str, 
                                message_type: str = "text", 
                                media_description: Optional[str] = None,
                                reply_to_message_id: Optional[int] = None) -> None:
    """Додає повідомлення до контексту чату"""
    conn = await _db_pool.get_connection()
    
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
    finally:
        await _db_pool.return_connection(conn)

async def get_recent_messages(chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Отримує останні повідомлення з чату з покращеною продуктивністю"""
    conn = await _db_pool.get_connection()
    
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
        
        # Повертаємо у хронологічному порядку
        return list(reversed(messages))
        
    except Exception as e:
        logger.error(f"Error getting recent messages: {e}")
        return []
    finally:
        await _db_pool.return_connection(conn)

async def build_context(chat_id: int, limit: int = 50) -> str:
    """Будує контекст для Gemini з покращеною структурою"""
    messages = await get_recent_messages(chat_id, limit)
    
    if not messages:
        return "Контекст порожній."
    
    context_lines = []
    for msg in messages:
        username = msg['full_name'] or msg['username'] or f"User{msg['user_id']}"
        
        if msg['message_type'] == 'text':
            context_lines.append(f"{username}: {msg['message_text']}")
        elif msg['media_description']:
            context_lines.append(f"{username}: [медіа: {msg['media_description']}]")
        else:
            context_lines.append(f"{username}: [медіа файл]")
    
    return "\n".join(context_lines)

async def cleanup_old_messages(chat_id: int, days_to_keep: int = 30) -> int:
    """Очищає старі повідомлення для оптимізації продуктивності"""
    conn = await _db_pool.get_connection()
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Підрахунок повідомлень для видалення
        async with conn.execute('''
            SELECT COUNT(*) FROM messages 
            WHERE chat_id = ? AND timestamp < ?
        ''', (chat_id, cutoff_date)) as cursor:
            count_result = await cursor.fetchone()
            count_to_delete = count_result[0] if count_result else 0
        
        # Видалення старих повідомлень
        await conn.execute('''
            DELETE FROM messages 
            WHERE chat_id = ? AND timestamp < ?
        ''', (chat_id, cutoff_date))
        
        await conn.commit()
        
        if count_to_delete > 0:
            logger.info(f"Cleaned up {count_to_delete} old messages from chat {chat_id}")
        
        return count_to_delete
        
    except Exception as e:
        logger.error(f"Error cleaning up old messages: {e}")
        return 0
    finally:
        await _db_pool.return_connection(conn)

async def get_chat_stats(chat_id: int) -> Dict[str, Any]:
    """Отримує статистику чату з покращеною продуктивністю"""
    conn = await _db_pool.get_connection()
    
    try:
        # Загальна кількість повідомлень
        async with conn.execute('''
            SELECT COUNT(*) FROM messages WHERE chat_id = ?
        ''', (chat_id,)) as cursor:
            total_messages = (await cursor.fetchone())[0]
        
        # Повідомлення за останні 7 днів
        week_ago = datetime.now() - timedelta(days=7)
        async with conn.execute('''
            SELECT COUNT(*) FROM messages 
            WHERE chat_id = ? AND timestamp > ?
        ''', (chat_id, week_ago)) as cursor:
            recent_messages = (await cursor.fetchone())[0]
        
        # Топ користувачі
        async with conn.execute('''
            SELECT full_name, COUNT(*) as msg_count
            FROM messages 
            WHERE chat_id = ? AND timestamp > ?
            GROUP BY user_id, full_name
            ORDER BY msg_count DESC
            LIMIT 5
        ''', (chat_id, week_ago)) as cursor:
            top_users = await cursor.fetchall()
        
        return {
            'total_messages': total_messages,
            'recent_messages': recent_messages,
            'top_users': [{'name': row[0], 'count': row[1]} for row in top_users]
        }
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        return {'total_messages': 0, 'recent_messages': 0, 'top_users': []}
    finally:
        await _db_pool.return_connection(conn)

async def log_analytics_event(chat_id: int, event_type: str, event_data: Optional[Dict[str, Any]] = None):
    """Логування аналітичних подій для моніторингу"""
    conn = await _db_pool.get_connection()
    
    try:
        data_json = json.dumps(event_data) if event_data else None
        
        await conn.execute('''
            INSERT INTO analytics (chat_id, event_type, event_data)
            VALUES (?, ?, ?)
        ''', (chat_id, event_type, data_json))
        
        await conn.commit()
        
    except Exception as e:
        logger.error(f"Error logging analytics event: {e}")
    finally:
        await _db_pool.return_connection(conn)

async def shutdown_database():
    """Коректне закриття всіх з'єднань"""
    await _db_pool.close_all()
    logger.info("Database connections closed")

# Backward compatibility functions
async def get_enhanced_context(chat_id: int, limit: int = 50) -> Dict[str, Any]:
    """Зворотна сумісність з enhanced_behavior модулем"""
    context_text = await build_context(chat_id, limit)
    messages = await get_recent_messages(chat_id, limit)
    
    return {
        'context': context_text,
        'message_count': len(messages),
        'recent_activity': len([m for m in messages if 
                              datetime.fromisoformat(m['timestamp'].replace('Z', '+00:00')).date() == datetime.now().date()])
    }

class AsyncContextManager:
    """Основний клас для управління асинхронним контекстом"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._pool = None
    
    async def initialize(self):
        """Ініціалізація менеджера"""
        if self._pool is None:
            self._pool = DatabaseConnectionPool(self.db_path)
            await self._pool.initialize()
    
    async def save_message(self, message: Any, media_id: Optional[str] = None, media_type: Optional[str] = None):
        """Збереження повідомлення"""
        await self.initialize()
        # Використовуємо функцію add_message_to_context як заглушку
        if hasattr(message, 'from_user') and message.from_user:
            await add_message_to_context(
                message.chat.id, 
                message.from_user.id, 
                message.from_user.full_name or "Unknown",
                message.text or ""
            )
    
    async def get_recent_messages(self, chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Отримання останніх повідомлень"""
        return await get_recent_messages(chat_id, limit)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Отримання статистики"""
        await self.initialize()
        try:
            async with await _db_pool.get_connection() as conn:
                cursor = await conn.execute("SELECT COUNT(*) FROM messages")
                result = await cursor.fetchone()
                total_messages = result[0] if result else 0
                
                cursor = await conn.execute("SELECT COUNT(DISTINCT chat_id) FROM messages")
                result = await cursor.fetchone()
                total_chats = result[0] if result else 0
                
                return {
                    'total_messages': total_messages,
                    'total_chats': total_chats,
                    'db_path': self.db_path
                }
        except Exception:
            return {
                'total_messages': 0,
                'total_chats': 0,
                'db_path': self.db_path
            }
    
    async def test_connection(self) -> bool:
        """Тест з'єднання з базою даних"""
        try:
            await self.initialize()
            async with await _db_pool.get_connection() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    async def migrate_from_sqlite(self) -> bool:
        """Міграція з синхронної SQLite БД"""
        # Поки що заглушка
        logger.info("Міграція з SQLite поки не реалізована")
        return True
