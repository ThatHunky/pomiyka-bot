# Покращений модуль кешування для Gemini відповідей
import hashlib
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import os
import aiosqlite

logger = logging.getLogger(__name__)

# Конфігурація кешу
CACHE_DB_PATH = os.path.join("data", "gemini_cache.db")
DEFAULT_TTL_HOURS = 24
SEMANTIC_SIMILARITY_THRESHOLD = 0.85

class GeminiCacheManager:
    """Розумний кеш для Gemini відповідей з семантичною схожістю"""
    
    def __init__(self, db_path: str = CACHE_DB_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        """Ініціалізація бази даних кешу"""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:
                return
                
            # Створюємо директорію
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            async with aiosqlite.connect(self.db_path) as conn:
                # Таблиця для точного кешування
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS exact_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt_hash TEXT UNIQUE NOT NULL,
                        prompt_text TEXT NOT NULL,
                        response_text TEXT NOT NULL,
                        context_hash TEXT,
                        tone_instruction TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME NOT NULL,
                        hit_count INTEGER DEFAULT 1,
                        last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблиця для семантичного кешування
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS semantic_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt_embedding TEXT NOT NULL,
                        prompt_keywords TEXT NOT NULL,
                        response_text TEXT NOT NULL,
                        similarity_score REAL DEFAULT 1.0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME NOT NULL,
                        hit_count INTEGER DEFAULT 1,
                        last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Індекси для продуктивності
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_exact_hash ON exact_cache(prompt_hash)
                ''')
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_exact_expires ON exact_cache(expires_at)
                ''')
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_semantic_keywords ON semantic_cache(prompt_keywords)
                ''')
                await conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_semantic_expires ON semantic_cache(expires_at)
                ''')
                
                await conn.commit()
            
            self._initialized = True
            logger.info("Gemini cache initialized")

    def _generate_hash(self, text: str, context: str = "", tone: str = "") -> str:
        """Генерує хеш для промпту з урахуванням контексту"""
        combined = f"{text}|{context}|{tone}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _extract_keywords(self, text: str) -> str:
        """Витягує ключові слова з тексту для семантичного пошуку"""
        # Прості ключові слова без NLP для початку
        import re
        words = re.findall(r'\b\w{3,}\b', text.lower())
        # Видаляємо стоп-слова
        stop_words = {'що', 'як', 'де', 'коли', 'чому', 'хто', 'які', 'яка', 'яке', 'що', 'чи', 'або', 'та', 'і', 'не'}
        keywords = [w for w in words if w not in stop_words]
        return ' '.join(sorted(set(keywords))[:10])  # Топ 10 унікальних слів

    async def get_cached_response(self, prompt: str, context: str = "", 
                                 tone_instruction: str = "") -> Optional[str]:
        """Отримує відповідь з кешу (точна або семантична відповідність)"""
        await self.initialize()
        
        # Спочатку шукаємо точний збіг
        exact_response = await self._get_exact_cache(prompt, context, tone_instruction)
        if exact_response:
            return exact_response
        
        # Якщо точного збігу немає, шукаємо семантично схожі
        semantic_response = await self._get_semantic_cache(prompt)
        return semantic_response

    async def _get_exact_cache(self, prompt: str, context: str, tone: str) -> Optional[str]:
        """Отримує точний збіг з кешу"""
        prompt_hash = self._generate_hash(prompt, context, tone)
        
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute('''
                SELECT response_text, hit_count FROM exact_cache 
                WHERE prompt_hash = ? AND expires_at > ?
            ''', (prompt_hash, datetime.now())) as cursor:
                result = await cursor.fetchone()
                
                if result:
                    response_text, hit_count = result
                    
                    # Оновлюємо статистику використання
                    await conn.execute('''
                        UPDATE exact_cache 
                        SET hit_count = hit_count + 1, last_accessed = ?
                        WHERE prompt_hash = ?
                    ''', (datetime.now(), prompt_hash))
                    await conn.commit()
                    
                    logger.debug(f"Cache hit (exact): {prompt_hash[:8]}... (hits: {hit_count + 1})")
                    return response_text
        
        return None

    async def _get_semantic_cache(self, prompt: str) -> Optional[str]:
        """Отримує семантично схожий результат з кешу"""
        keywords = self._extract_keywords(prompt)
        if not keywords:
            return None
        
        async with aiosqlite.connect(self.db_path) as conn:
            # Простий пошук по ключових словах
            keyword_parts = keywords.split()[:5]  # Перші 5 слів
            
            for keyword in keyword_parts:
                async with conn.execute('''
                    SELECT response_text, prompt_keywords, hit_count 
                    FROM semantic_cache 
                    WHERE prompt_keywords LIKE ? AND expires_at > ?
                    ORDER BY hit_count DESC
                    LIMIT 3
                ''', (f'%{keyword}%', datetime.now())) as cursor:
                    results = await cursor.fetchall()
                    
                    for response_text, cached_keywords, hit_count in results:
                        # Простий підрахунок схожості через перетин ключових слів
                        cached_set = set(cached_keywords.split())
                        prompt_set = set(keywords.split())
                        similarity = len(cached_set & prompt_set) / len(cached_set | prompt_set)
                        
                        if similarity >= SEMANTIC_SIMILARITY_THRESHOLD:
                            logger.debug(f"Cache hit (semantic): similarity={similarity:.2f}")
                            return response_text
        
        return None

    async def cache_response(self, prompt: str, response: str, context: str = "", 
                           tone_instruction: str = "", ttl_hours: int = DEFAULT_TTL_HOURS):
        """Кешує відповідь Gemini"""
        await self.initialize()
        
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        # Кешуємо точний збіг
        await self._cache_exact(prompt, response, context, tone_instruction, expires_at)
        
        # Кешуємо для семантичного пошуку
        await self._cache_semantic(prompt, response, expires_at)

    async def _cache_exact(self, prompt: str, response: str, context: str, 
                          tone: str, expires_at: datetime):
        """Кешує точний збіг"""
        prompt_hash = self._generate_hash(prompt, context, tone)
        context_hash = hashlib.sha256(context.encode()).hexdigest() if context else None
        
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute('''
                    INSERT OR REPLACE INTO exact_cache 
                    (prompt_hash, prompt_text, response_text, context_hash, tone_instruction, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (prompt_hash, prompt[:1000], response, context_hash, tone, expires_at))
                await conn.commit()
            except Exception as e:
                logger.error(f"Error caching exact response: {e}")

    async def _cache_semantic(self, prompt: str, response: str, expires_at: datetime):
        """Кешує для семантичного пошуку"""
        keywords = self._extract_keywords(prompt)
        if not keywords:
            return
        
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute('''
                    INSERT INTO semantic_cache 
                    (prompt_embedding, prompt_keywords, response_text, expires_at)
                    VALUES (?, ?, ?, ?)
                ''', ("", keywords, response, expires_at))  # embedding можна додати пізніше
                await conn.commit()
            except Exception as e:
                logger.error(f"Error caching semantic response: {e}")

    async def cleanup_expired(self) -> int:
        """Видаляє застарілі записи з кешу"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as conn:
            # Видаляємо застарілі записи
            cursor1 = await conn.execute('''
                DELETE FROM exact_cache WHERE expires_at < ?
            ''', (datetime.now(),))
            exact_deleted = cursor1.rowcount
            
            cursor2 = await conn.execute('''
                DELETE FROM semantic_cache WHERE expires_at < ?
            ''', (datetime.now(),))
            semantic_deleted = cursor2.rowcount
            
            await conn.commit()
            
            total_deleted = exact_deleted + semantic_deleted
            if total_deleted > 0:
                logger.info(f"Cleaned up {total_deleted} expired cache entries")
            
            return total_deleted

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Отримує статистику кешу"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as conn:
            # Статистика точного кешу
            async with conn.execute('''
                SELECT COUNT(*), SUM(hit_count), AVG(hit_count) 
                FROM exact_cache WHERE expires_at > ?
            ''', (datetime.now(),)) as cursor:
                exact_stats = await cursor.fetchone()
            
            # Статистика семантичного кешу
            async with conn.execute('''
                SELECT COUNT(*), SUM(hit_count), AVG(hit_count) 
                FROM semantic_cache WHERE expires_at > ?
            ''', (datetime.now(),)) as cursor:
                semantic_stats = await cursor.fetchone()
            
            return {
                'exact_cache': {
                    'entries': exact_stats[0] or 0,
                    'total_hits': exact_stats[1] or 0,
                    'avg_hits': round(exact_stats[2] or 0, 2)
                },
                'semantic_cache': {
                    'entries': semantic_stats[0] or 0,
                    'total_hits': semantic_stats[1] or 0,
                    'avg_hits': round(semantic_stats[2] or 0, 2)
                }
            }

    async def clear_cache(self):
        """Очищає весь кеш"""
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute('DELETE FROM exact_cache')
            await conn.execute('DELETE FROM semantic_cache')
            await conn.commit()
            
        logger.info("Gemini cache cleared")

# Глобальний екземпляр кеш-менеджера
cache_manager = GeminiCacheManager()

# Функції для зворотної сумісності
async def get_cached_response(prompt: str, context: str = "", tone_instruction: str = "") -> Optional[str]:
    """Отримує відповідь з кешу"""
    return await cache_manager.get_cached_response(prompt, context, tone_instruction)

async def cache_response(prompt: str, response: str, context: str = "", 
                        tone_instruction: str = "", ttl_hours: int = DEFAULT_TTL_HOURS):
    """Кешує відповідь"""
    await cache_manager.cache_response(prompt, response, context, tone_instruction, ttl_hours)

async def cleanup_cache() -> int:
    """Очищає застарілі записи"""
    return await cache_manager.cleanup_expired()

async def get_cache_stats() -> Dict[str, Any]:
    """Отримує статистику кешу"""
    return await cache_manager.get_cache_stats()

# Псевдонім для зворотної сумісності
GeminiCache = GeminiCacheManager
