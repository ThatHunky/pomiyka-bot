"""
Модуль персоналізації для адаптації бота під кожного користувача.
Вивчає уподобання, стиль спілкування та налаштовує відповіді.
"""

import json
import logging
import asyncio
import aiosqlite
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)

# Async lock для thread safety
_personalization_lock = asyncio.Lock()


@dataclass
class UserPreferences:
    """Уподобання користувача"""
    user_id: int
    username: str
    communication_style: str = "neutral"  # friendly, formal, casual, humorous
    preferred_topics: List[str] = field(default_factory=list)
    reaction_preferences: Dict[str, float] = field(default_factory=dict)  # emoji -> preference score
    response_length_pref: str = "medium"  # short, medium, long
    humor_level: float = 0.5  # 0.0 - serious, 1.0 - very humorous
    ai_interaction_style: str = "balanced"  # minimal, balanced, active
    language_complexity: str = "medium"  # simple, medium, complex
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "smart_reactions": True,
        "spontaneous_messages": True,
        "analytics_mentions": False
    })
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class InteractionPattern:
    """Патерн взаємодії користувача"""
    user_id: int
    message_times: List[int] = field(default_factory=list)  # години активності
    message_lengths: List[int] = field(default_factory=list)
    emoji_usage: Dict[str, int] = field(default_factory=dict)
    topic_interests: Dict[str, int] = field(default_factory=dict)
    response_patterns: Dict[str, int] = field(default_factory=dict)  # типи відповідей
    sentiment_history: List[float] = field(default_factory=list)


class PersonalizationManager:
    """Менеджер персоналізації"""
    
    def __init__(self, db_path: str = "data/personalization.db"):
        self.db_path = db_path
        self.user_preferences: Dict[int, UserPreferences] = {}
        self.interaction_patterns: Dict[int, InteractionPattern] = {}
        self._db_initialized = False  # Instance-specific initialization flag
        
        # Конфігурація для аналізу тем
        self.topic_keywords = {
            "технології": ["код", "програмування", "ком'ютер", "інтернет", "сайт", "додаток"],
            "спорт": ["футбол", "спорт", "гра", "тренування", "матч", "команда"],
            "їжа": ["їжа", "готувати", "рецепт", "смачно", "ресторан", "кафе"],
            "музика": ["музика", "пісня", "концерт", "група", "співати", "інструмент"],
            "фільми": ["фільм", "кіно", "серіал", "актор", "режисер", "дивитися"],
            "подорожі": ["подорож", "відпочинок", "море", "гори", "країна", "туризм"],
            "навчання": ["навчання", "університет", "школа", "курси", "знання", "вивчати"],
            "робота": ["робота", "офіс", "проект", "зарплата", "карьера", "колеги"],
            "хобі": ["хобі", "захоплення", "колекція", "творчість", "майстерність"],
            "новини": ["новини", "події", "політика", "суспільство", "світ"]
        }

    async def _init_database(self):
        """Ініціалізація бази даних персоналізації"""
        async with _personalization_lock:
            if self._db_initialized:
                return
                
            try:
                async with aiosqlite.connect(self.db_path) as conn:
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS user_preferences (
                            user_id INTEGER PRIMARY KEY,
                            data TEXT,
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS interaction_patterns (
                            user_id INTEGER PRIMARY KEY,
                            data TEXT,
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS personalization_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            event_type TEXT,
                            event_data TEXT,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Створюємо індекси для кращої продуктивності
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id)")
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_interaction_patterns_user ON interaction_patterns(user_id)")
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_personalization_events_user ON personalization_events(user_id)")
                    await conn.execute("CREATE INDEX IF NOT EXISTS idx_personalization_events_time ON personalization_events(timestamp)")
                    
                    await conn.commit()
                    logger.info("База даних персоналізації ініціалізована з індексами")
                    
            except Exception as e:
                logger.error(f"Помилка ініціалізації БД персоналізації: {e}")

    async def _ensure_db_initialized(self):
        """Переконується, що БД ініціалізована"""
        if not self._db_initialized:
            await self._init_database()
            self._db_initialized = True

    async def _load_user_data(self):
        """Завантажує дані користувачів з бази"""
        try:
            await self._ensure_db_initialized()
            
            async with _personalization_lock:
                async with aiosqlite.connect(self.db_path) as conn:
                    # Завантаження уподобань
                    async with conn.execute("SELECT user_id, data FROM user_preferences") as cursor:
                        async for row in cursor:
                            user_id, data_json = row
                            try:
                                data = json.loads(data_json)
                                preferences = UserPreferences(**data)
                                self.user_preferences[user_id] = preferences
                            except Exception as e:
                                logger.error(f"Помилка завантаження уподобань користувача {user_id}: {e}")
                    
                    # Завантаження патернів
                    async with conn.execute("SELECT user_id, data FROM interaction_patterns") as cursor:
                        async for row in cursor:
                            user_id, data_json = row
                            try:
                                data = json.loads(data_json)
                                pattern = InteractionPattern(**data)
                                self.interaction_patterns[user_id] = pattern
                            except Exception as e:
                                logger.error(f"Помилка завантаження патернів користувача {user_id}: {e}")
                    
                    logger.info(f"Завантажено дані для {len(self.user_preferences)} користувачів")
                
        except Exception as e:
            logger.error(f"Помилка завантаження даних персоналізації: {e}")

    async def process_user_message(self, user_id: int, username: str, 
                                 text: str, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """Обробляє повідомлення користувача для персоналізації"""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Ініціалізація користувача, якщо потрібно
            if user_id not in self.user_preferences:
                await self._init_user(user_id, username)
            
            # Оновлення патернів взаємодії
            await self._update_interaction_patterns(user_id, text, timestamp)
            
            # Аналіз тексту для уподобань
            await self._analyze_message_for_preferences(user_id, text)
            
            # Збереження події
            await self._save_personalization_event(user_id, "message_processed", {
                "text_length": len(text),
                "timestamp": timestamp.isoformat()
            })
            
            return {
                "processed": True,
                "user_id": user_id,
                "updated_preferences": True
            }
            
        except Exception as e:
            logger.error(f"Помилка обробки повідомлення для персоналізації: {e}")
            return {"processed": False, "error": str(e)}

    async def _init_user(self, user_id: int, username: str):
        """Ініціалізує нового користувача"""
        preferences = UserPreferences(user_id=user_id, username=username)
        pattern = InteractionPattern(user_id=user_id)
        
        self.user_preferences[user_id] = preferences
        self.interaction_patterns[user_id] = pattern
        
        await self._save_user_preferences(user_id)
        await self._save_interaction_patterns(user_id)
        
        logger.info(f"Ініціалізовано нового користувача: {username} ({user_id})")

    async def _update_interaction_patterns(self, user_id: int, text: str, timestamp: datetime):
        """Оновлює патерни взаємодії користувача"""
        if user_id not in self.interaction_patterns:
            return
        
        pattern = self.interaction_patterns[user_id]
        
        # Час активності
        hour = timestamp.hour
        pattern.message_times.append(hour)
        if len(pattern.message_times) > 100:  # Обмежуємо розмір
            pattern.message_times = pattern.message_times[-100:]
        
        # Довжина повідомлень
        pattern.message_lengths.append(len(text))
        if len(pattern.message_lengths) > 100:
            pattern.message_lengths = pattern.message_lengths[-100:]
        
        # Емодзі
        emojis = self._extract_emojis(text)
        for emoji in emojis:
            pattern.emoji_usage[emoji] = pattern.emoji_usage.get(emoji, 0) + 1
        
        # Теми
        topics = self._detect_topics(text)
        for topic in topics:
            pattern.topic_interests[topic] = pattern.topic_interests.get(topic, 0) + 1
        
        await self._save_interaction_patterns(user_id)

    async def _analyze_message_for_preferences(self, user_id: int, text: str):
        """Аналізує повідомлення для визначення уподобань"""
        if user_id not in self.user_preferences:
            return
        
        preferences = self.user_preferences[user_id]
        
        # Визначення стилю спілкування
        style = self._detect_communication_style(text)
        if style != "neutral":
            preferences.communication_style = style
        
        # Рівень гумору
        humor_score = self._detect_humor_level(text)
        if humor_score > 0:
            # Плавно оновлюємо рівень гумору
            preferences.humor_level = (preferences.humor_level * 0.8 + humor_score * 0.2)
        
        # Складність мови
        complexity = self._detect_language_complexity(text)
        if complexity != "medium":
            preferences.language_complexity = complexity
        
        # Оновлення часу
        preferences.last_updated = datetime.now()
        
        await self._save_user_preferences(user_id)

    def _extract_emojis(self, text: str) -> List[str]:
        """Витягує емодзі з тексту"""
        emojis = []
        for char in text:
            if ord(char) > 0x1F600:  # Базовий діапазон емодзі
                emojis.append(char)
        return emojis

    def _detect_topics(self, text: str) -> List[str]:
        """Визначає теми в тексті"""
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in self.topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics

    def _detect_communication_style(self, text: str) -> str:
        """Визначає стиль спілкування"""
        text_lower = text.lower()
        
        # Формальний стиль
        formal_markers = ["будь ласка", "дякую", "вибачте", "шановний"]
        if any(marker in text_lower for marker in formal_markers):
            return "formal"
        
        # Дружний стиль
        friendly_markers = ["привіт", "як справи", "дуже рад", "круто", "супер"]
        if any(marker in text_lower for marker in friendly_markers):
            return "friendly"
        
        # Casual стиль
        casual_markers = ["хай", "окей", "ага", "неа", "йо"]
        if any(marker in text_lower for marker in casual_markers):
            return "casual"
        
        return "neutral"

    def _detect_humor_level(self, text: str) -> float:
        """Визначає рівень гумору"""
        text_lower = text.lower()
        
        humor_markers = ["хаха", "лол", "жарт", "смішно", "прикол", "угар", "😂", "😄", "😁"]
        humor_count = sum(1 for marker in humor_markers if marker in text_lower)
        
        # Нормалізуємо до 0-1
        return min(humor_count / 3.0, 1.0)

    def _detect_language_complexity(self, text: str) -> str:
        """Визначає складність мови"""
        words = text.split()
        
        if len(words) < 5:
            return "simple"
        elif len(words) > 20:
            return "complex"
        
        # Перевіряємо наявність складних слів
        complex_words = sum(1 for word in words if len(word) > 8)
        if complex_words > len(words) * 0.3:
            return "complex"
        elif complex_words == 0:
            return "simple"
        
        return "medium"

    async def get_personalized_response_config(self, user_id: int) -> Dict[str, Any]:
        """Отримує персоналізовану конфігурацію для відповіді"""
        try:
            if user_id not in self.user_preferences:
                return self._get_default_response_config()
            
            preferences = self.user_preferences[user_id]
            pattern = self.interaction_patterns.get(user_id)
            
            # Визначаємо найактивніший час
            most_active_hour = 12
            if pattern and pattern.message_times:
                hour_counter = Counter(pattern.message_times)
                most_active_hour = hour_counter.most_common(1)[0][0]
            
            # Найпопулярніші теми
            top_topics = []
            if pattern and pattern.topic_interests:
                topic_counter = Counter(pattern.topic_interests)
                top_topics = [topic for topic, _ in topic_counter.most_common(3)]
            
            return {
                "communication_style": preferences.communication_style,
                "humor_level": preferences.humor_level,
                "language_complexity": preferences.language_complexity,
                "response_length": preferences.response_length_pref,
                "ai_style": preferences.ai_interaction_style,
                "preferred_topics": top_topics,
                "most_active_hour": most_active_hour,
                "notification_preferences": preferences.notification_preferences
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання персоналізованої конфігурації: {e}")
            return self._get_default_response_config()

    def _get_default_response_config(self) -> Dict[str, Any]:
        """Повертає конфігурацію за замовчуванням"""
        return {
            "communication_style": "neutral",
            "humor_level": 0.5,
            "language_complexity": "medium",
            "response_length": "medium",
            "ai_style": "balanced",
            "preferred_topics": [],
            "most_active_hour": 12,
            "notification_preferences": {
                "smart_reactions": True,
                "spontaneous_messages": True,
                "analytics_mentions": False
            }
        }

    async def should_send_notification(self, user_id: int, notification_type: str) -> bool:
        """Перевіряє, чи слід надсилати сповіщення користувачу"""
        if user_id not in self.user_preferences:
            return True  # За замовчуванням дозволяємо
        
        preferences = self.user_preferences[user_id]
        return preferences.notification_preferences.get(notification_type, True)

    async def update_user_preference(self, user_id: int, preference_key: str, 
                                   preference_value: Any) -> bool:
        """Оновлює уподобання користувача"""
        try:
            if user_id not in self.user_preferences:
                return False
            
            preferences = self.user_preferences[user_id]
            
            if hasattr(preferences, preference_key):
                setattr(preferences, preference_key, preference_value)
                preferences.last_updated = datetime.now()
                
                await self._save_user_preferences(user_id)
                
                await self._save_personalization_event(user_id, "preference_updated", {
                    "key": preference_key,
                    "value": str(preference_value)
                })
                
                logger.info(f"Оновлено уподобання користувача {user_id}: {preference_key} = {preference_value}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Помилка оновлення уподобань: {e}")
            return False

    async def _save_user_preferences(self, user_id: int):
        """Зберігає уподобання користувача"""
        try:
            if user_id not in self.user_preferences:
                return
            
            await self._ensure_db_initialized()
            preferences = self.user_preferences[user_id]
            data_json = json.dumps(asdict(preferences), default=str, ensure_ascii=False)
            
            async with _personalization_lock:
                async with aiosqlite.connect(self.db_path) as conn:
                    await conn.execute("""
                        INSERT OR REPLACE INTO user_preferences (user_id, data, last_updated)
                        VALUES (?, ?, ?)
                    """, (user_id, data_json, datetime.now()))
                    await conn.commit()
            
        except Exception as e:
            logger.error(f"Помилка збереження уподобань: {e}")

    async def _save_interaction_patterns(self, user_id: int):
        """Зберігає патерни взаємодії"""
        try:
            if user_id not in self.interaction_patterns:
                return
            
            await self._ensure_db_initialized()
            pattern = self.interaction_patterns[user_id]
            data_json = json.dumps(asdict(pattern), default=str, ensure_ascii=False)
            
            async with _personalization_lock:
                async with aiosqlite.connect(self.db_path) as conn:
                    await conn.execute("""
                        INSERT OR REPLACE INTO interaction_patterns (user_id, data, last_updated)
                        VALUES (?, ?, ?)
                    """, (user_id, data_json, datetime.now()))
                    await conn.commit()
            
        except Exception as e:
            logger.error(f"Помилка збереження патернів: {e}")

    async def _save_personalization_event(self, user_id: int, event_type: str, event_data: Dict[str, Any]):
        """Зберігає подію персоналізації"""
        try:
            await self._ensure_db_initialized()
            data_json = json.dumps(event_data, default=str, ensure_ascii=False)
            
            async with _personalization_lock:
                async with aiosqlite.connect(self.db_path) as conn:
                    await conn.execute("""
                        INSERT INTO personalization_events (user_id, event_type, event_data)
                        VALUES (?, ?, ?)
                    """, (user_id, event_type, data_json))
                    await conn.commit()
            
        except Exception as e:
            logger.error(f"Помилка збереження події персоналізації: {e}")

    async def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """Отримує статистику користувача"""
        try:
            preferences = self.user_preferences.get(user_id)
            pattern = self.interaction_patterns.get(user_id)
            
            if not preferences or not pattern:
                return {"error": "Користувач не знайдений"}
            
            # Аналіз активності по годинах
            hour_activity: Counter[int] = Counter(pattern.message_times) if pattern.message_times else Counter()
            
            # Топ емодзі
            top_emojis = Counter(pattern.emoji_usage).most_common(5) if pattern.emoji_usage else []
            
            # Топ теми
            top_topics = Counter(pattern.topic_interests).most_common(5) if pattern.topic_interests else []
            
            return {
                "user_id": user_id,
                "username": preferences.username,
                "communication_style": preferences.communication_style,
                "humor_level": preferences.humor_level,
                "language_complexity": preferences.language_complexity,
                "total_messages": len(pattern.message_times),
                "avg_message_length": sum(pattern.message_lengths) / len(pattern.message_lengths) if pattern.message_lengths else 0,
                "most_active_hours": dict(hour_activity.most_common(3)),
                "favorite_emojis": dict(top_emojis),
                "favorite_topics": dict(top_topics),
                "last_updated": preferences.last_updated.isoformat() if preferences.last_updated else None
            }
            
        except Exception as e:
            logger.error(f"Помилка отримання статистики користувача: {e}")
            return {"error": str(e)}

    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Очищення старих даних персоналізації"""
        try:
            await self._ensure_db_initialized()
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            async with _personalization_lock:
                async with aiosqlite.connect(self.db_path) as conn:
                    # Очищення старих подій
                    cursor = await conn.execute("""
                        DELETE FROM personalization_events 
                        WHERE timestamp < ?
                    """, (cutoff_date,))
                    
                    deleted_events = cursor.rowcount or 0
                    await conn.commit()
                    
                    # Очищення патернів користувачів (обмежуємо розміри списків)
                    # Групуємо оновлення для зменшення кількості async викликів
                    patterns_to_update: List[int] = []
                    
                    for user_id, pattern in self.interaction_patterns.items():
                        pattern_updated = False
                        
                        if len(pattern.message_times) > 200:
                            pattern.message_times = pattern.message_times[-200:]
                            pattern_updated = True
                        if len(pattern.message_lengths) > 200:
                            pattern.message_lengths = pattern.message_lengths[-200:]
                            pattern_updated = True
                        if len(pattern.sentiment_history) > 100:
                            pattern.sentiment_history = pattern.sentiment_history[-100:]
                            pattern_updated = True
                        
                        if pattern_updated:
                            patterns_to_update.append(user_id)
                    
                    # Збереження оновлених патернів пакетно
                    for user_id in patterns_to_update:
                        await self._save_interaction_patterns(user_id)
                        # Дозволяємо іншим async задачам виконатись
                        await asyncio.sleep(0.001)
                    
                    logger.info(f"Очищено {deleted_events} старих подій персоналізації та {len(patterns_to_update)} патернів")
                    return deleted_events
                
        except Exception as e:
            logger.error(f"Помилка очищення старих даних персоналізації: {e}")
            return 0

    def get_health_status(self) -> Dict[str, Any]:
        """Повертає стан модуля персоналізації"""
        try:
            return {
                "status": "healthy",
                "users_count": len(self.user_preferences),
                "patterns_count": len(self.interaction_patterns),
                "database_path": self.db_path,
                "topics_configured": len(self.topic_keywords)
            }
            
        except Exception as e:
            logger.error(f"Помилка перевірки стану персоналізації: {e}")
            return {"status": "error", "error": str(e)}

    async def initialize(self):
        """Асинхронна ініціалізація менеджера персоналізації"""
        try:
            await self._init_database()
            await self._load_user_data()
            logger.info("PersonalizationManager успішно ініціалізовано")
        except Exception as e:
            logger.error(f"Помилка ініціалізації PersonalizationManager: {e}")


# Фабрика для створення екземпляру
async def create_personalization_manager(db_path: str = "data/personalization.db") -> PersonalizationManager:
    """Створює та ініціалізує екземпляр PersonalizationManager"""
    manager = PersonalizationManager(db_path)
    await manager.initialize()
    return manager
