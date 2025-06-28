"""
Адаптер для поступової міграції до асинхронної бази даних
Цей модуль дозволяє використовувати як стару синхронну, так і нову асинхронну БД
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from aiogram.types import Message
import os

# Спробуємо імпорти
try:
    from .context_async import AsyncContextManager
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False
    
from .context_sqlite import (
    init_db as sync_init_db,
    save_message as sync_save_message,
    get_recent_messages as sync_get_recent_messages,
    get_context as sync_get_context,
    get_chat_stats as sync_get_chat_stats,
    get_global_stats as sync_get_global_stats
)

logger = logging.getLogger(__name__)

class ContextAdapter:
    """Адаптер для роботи з контекстом, який підтримує обидва типи БД"""
    
    def __init__(self, use_async: Optional[bool] = None):
        """
        Ініціалізація адаптера
        
        Args:
            use_async: Чи використовувати асинхронну БД. Якщо None, то автовизначення
        """
        if use_async is None:
            # Автовизначення: використовуємо async якщо доступно та є змінна середовища
            self.use_async = ASYNC_AVAILABLE and os.getenv('USE_ASYNC_DB', 'false').lower() == 'true'
        else:
            self.use_async = use_async and ASYNC_AVAILABLE
            
        self._async_manager = None
        
        if self.use_async:
            logger.info("🔄 Використовується асинхронна база даних")
        else:
            logger.info("📂 Використовується синхронна база даних")
    
    async def _get_async_manager(self) -> 'AsyncContextManager':
        """Отримати менеджер асинхронної БД"""
        if self._async_manager is None:
            from .context_async import AsyncContextManager
            self._async_manager = AsyncContextManager()
            await self._async_manager.initialize()
        return self._async_manager
    
    def init_db(self) -> None:
        """Ініціалізація бази даних"""
        if self.use_async:
            # Для асинхронної БД ініціалізація відбувається при першому використанні
            pass
        else:
            sync_init_db()
    
    def save_message(self, message: Message, media_id: Optional[str] = None, media_type: Optional[str] = None) -> None:
        """Збереження повідомлення"""
        if self.use_async:
            # Для асинхронних операцій використовуємо фонову задачу
            asyncio.create_task(self._async_save_message(message, media_id, media_type))
        else:
            sync_save_message(message, media_id, media_type)
    
    async def _async_save_message(self, message: Message, media_id: Optional[str] = None, media_type: Optional[str] = None) -> None:
        """Асинхронне збереження повідомлення"""
        try:
            manager = await self._get_async_manager()
            await manager.save_message(message, media_id, media_type)
        except Exception as e:
            logger.error(f"Помилка збереження повідомлення асинхронно: {e}")
            # Fallback до синхронної БД
            sync_save_message(message, media_id, media_type)
    
    async def get_recent_messages(self, chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Отримання останніх повідомлень"""
        if self.use_async:
            try:
                manager = await self._get_async_manager()
                return await manager.get_recent_messages(chat_id, limit)
            except Exception as e:
                logger.error(f"Помилка отримання повідомлень асинхронно: {e}")
                # Fallback до синхронної БД
                return sync_get_recent_messages(chat_id, limit)
        else:
            return sync_get_recent_messages(chat_id, limit)
    
    def get_recent_messages_sync(self, chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Синхронна версія отримання останніх повідомлень"""
        if self.use_async:
            # Запускаємо асинхронну функцію синхронно
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Якщо loop вже запущений, створюємо нову задачу
                    return asyncio.run_coroutine_threadsafe(
                        self.get_recent_messages(chat_id, limit), loop
                    ).result(timeout=10.0)
                else:
                    return asyncio.run(self.get_recent_messages(chat_id, limit))
            except Exception as e:
                logger.error(f"Помилка синхронного виклику асинхронної функції: {e}")
                return sync_get_recent_messages(chat_id, limit)
        else:
            return sync_get_recent_messages(chat_id, limit)
    
    async def get_messages_by_chat(self, chat_id: int, limit: int = 1000) -> List[Dict[str, Any]]:
        """Отримання повідомлень чату"""
        if self.use_async:
            try:
                manager = await self._get_async_manager()
                return await manager.get_recent_messages(chat_id, limit)
            except Exception as e:
                logger.error(f"Помилка отримання повідомлень чату асинхронно: {e}")
                return sync_get_recent_messages(chat_id, limit)
        else:
            return sync_get_recent_messages(chat_id, limit)
    
    async def clear_context(self, chat_id: int) -> None:
        """Очищення контексту чату"""
        if self.use_async:
            try:
                manager = await self._get_async_manager()
                # Поки що використовуємо синхронну версію
                logger.info(f"Очищення контексту для чату {chat_id} (поки що недоступно)")
            except Exception as e:
                logger.error(f"Помилка очищення контексту асинхронно: {e}")
        else:
            logger.info(f"Очищення контексту для чату {chat_id} (функція недоступна в синхронній версії)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Отримання статистики"""
        stats = {
            "adapter_type": "async" if self.use_async else "sync",
            "async_available": ASYNC_AVAILABLE
        }
        
        if self.use_async and self._async_manager:
            try:
                # Отримуємо статистику з асинхронного менеджера
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    stats["async_stats"] = "Available in async context"
                else:
                    async_stats = asyncio.run(self._get_async_stats())
                    stats.update(async_stats)
            except Exception as e:
                stats["async_stats_error"] = str(e)
        
        return stats
    
    async def _get_async_stats(self) -> Dict[str, Any]:
        """Отримання статистики асинхронної БД"""
        if self._async_manager:
            return await self._async_manager.get_stats()
        return {}
    
    async def migrate_to_async(self) -> bool:
        """Міграція даних до асинхронної БД"""
        if not ASYNC_AVAILABLE:
            logger.error("Асинхронна БД недоступна для міграції")
            return False
        
        try:
            manager = await self._get_async_manager()
            success = await manager.migrate_from_sqlite()
            if success:
                self.use_async = True
                logger.info("✅ Міграція до асинхронної БД завершена успішно")
            return success
        except Exception as e:
            logger.error(f"Помилка міграції до асинхронної БД: {e}")
            return False


# Глобальний екземпляр адаптера
_context_adapter = None

def get_context_adapter() -> ContextAdapter:
    """Отримати глобальний екземпляр адаптера контексту"""
    global _context_adapter
    if _context_adapter is None:
        _context_adapter = ContextAdapter()
    return _context_adapter

# Функції-обгортки для зворотної сумісності
def init_db() -> None:
    """Ініціалізація бази даних"""
    adapter = get_context_adapter()
    adapter.init_db()

def save_message(message: Message, media_id: Optional[str] = None, media_type: Optional[str] = None) -> None:
    """Збереження повідомлення"""
    adapter = get_context_adapter()
    adapter.save_message(message, media_id, media_type)

def get_recent_messages(chat_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Отримання останніх повідомлень (синхронна версія)"""
    adapter = get_context_adapter()
    return adapter.get_recent_messages_sync(chat_id, limit)

def get_messages_by_chat(chat_id: int, limit: int = 1000) -> List[Dict[str, Any]]:
    """Отримання повідомлень чату"""
    adapter = get_context_adapter()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Використовуємо синхронну версію як fallback
            return sync_get_recent_messages(chat_id, limit)
        else:
            return asyncio.run(adapter.get_messages_by_chat(chat_id, limit))
    except Exception as e:
        logger.error(f"Помилка отримання повідомлень чату: {e}")
        return sync_get_recent_messages(chat_id, limit)

def clear_context(chat_id: int) -> None:
    """Очищення контексту чату"""
    adapter = get_context_adapter()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(adapter.clear_context(chat_id))
        else:
            asyncio.run(adapter.clear_context(chat_id))
    except Exception as e:
        logger.error(f"Помилка очищення контексту: {e}")
