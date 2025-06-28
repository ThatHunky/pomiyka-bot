"""
Аналітичний движок для глибокого аналізу чатів та користувачів.
Збирає метрики, виявляє закономірності та надає інсайти.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class ChatMetrics:
    """Метрики чату"""
    chat_id: int
    total_messages: int = 0
    active_users: int = 0
    avg_message_length: float = 0.0
    most_active_hour: int = 0
    emoji_usage: Optional[Dict[str, int]] = None
    word_frequency: Optional[Dict[str, int]] = None
    sentiment_score: float = 0.0
    activity_trend: str = "stable"  # growing, declining, stable
    
    def __post_init__(self):
        if self.emoji_usage is None:
            self.emoji_usage = {}
        if self.word_frequency is None:
            self.word_frequency = {}


@dataclass
class UserAnalytics:
    """Аналітика користувача"""
    user_id: int
    username: str
    message_count: int = 0
    avg_message_length: float = 0.0
    most_active_time: str = "unknown"
    engagement_score: float = 0.0
    communication_style: str = "neutral"  # friendly, neutral, aggressive
    favorite_emojis: Optional[List[str]] = None
    topics_of_interest: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.favorite_emojis is None:
            self.favorite_emojis = []
        if self.topics_of_interest is None:
            self.topics_of_interest = []


@dataclass
class TrendAnalysis:
    """Аналіз трендів"""
    period: str  # daily, weekly, monthly
    message_trend: List[Tuple[str, int]]  # (date, count)
    user_activity_trend: List[Tuple[str, int]]  # (date, active_users)
    popular_topics: List[Tuple[str, int]]  # (topic, frequency)
    engagement_trend: List[Tuple[str, float]]  # (date, score)


class AnalyticsEngine:
    """Аналітичний движок"""
    
    def __init__(self, db_path: str = "data/analytics.db"):
        self.db_path = db_path
        self.chat_cache: Dict[int, ChatMetrics] = {}
        self.user_cache: Dict[int, UserAnalytics] = {}
        
        # Ініціалізація БД
        self._init_database()
        
        # Конфігурація аналізу
        self.stop_words = {
            "і", "в", "на", "з", "до", "по", "від", "за", "про", "при", "під",
            "над", "через", "для", "без", "біля", "коло", "крім", "між", "серед",
            "та", "а", "але", "або", "чи", "що", "як", "де", "коли", "чому"
        }
        
        # Позитивні та негативні слова для sentiment аналізу
        self.positive_words = {
            "добре", "класно", "супер", "чудово", "відмінно", "круто", "любов",
            "дякую", "спасибі", "молодець", "браво", "вау", "кайф", "топ"
        }
        
        self.negative_words = {
            "погано", "жахливо", "ненавиджу", "дурно", "паскуда", "лайно",
            "біда", "проблема", "помилка", "провал", "катастрофа"
        }

    def _init_database(self):
        """Ініціалізація бази даних аналітики"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chat_analytics (
                        chat_id INTEGER PRIMARY KEY,
                        data TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_analytics (
                        user_id INTEGER PRIMARY KEY,
                        data TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS message_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        user_id INTEGER,
                        message_length INTEGER,
                        timestamp TIMESTAMP,
                        hour INTEGER,
                        has_emoji BOOLEAN,
                        emoji_count INTEGER,
                        word_count INTEGER,
                        sentiment REAL
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_chat_time 
                    ON message_events(chat_id, timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_user_time 
                    ON message_events(user_id, timestamp)
                """)
                
                logger.info("База даних аналітики ініціалізована")
                
        except Exception as e:
            logger.error(f"Помилка ініціалізації БД аналітики: {e}")

    async def process_message(self, chat_id: int, user_id: int, text: str, 
                            user_name: str = "Unknown") -> Dict[str, Any]:
        """Обробляє повідомлення для аналітики"""
        try:
            # Базові метрики
            message_length = len(text) if text else 0
            word_count = len(text.split()) if text else 0
            current_time = datetime.now()
            hour = current_time.hour
            
            # Аналіз емодзі
            emoji_count = self._count_emojis(text)
            has_emoji = emoji_count > 0
            
            # Sentiment аналіз
            sentiment = await self._analyze_sentiment(text)
            
            # Збереження події
            await self._save_message_event(
                chat_id, user_id, message_length, current_time,
                hour, has_emoji, emoji_count, word_count, sentiment
            )
            
            # Оновлення кешу
            await self._update_chat_cache(chat_id, text, current_time)
            await self._update_user_cache(user_id, user_name, text, current_time)
            
            return {
                "processed": True,
                "metrics": {
                    "length": message_length,
                    "words": word_count,
                    "emojis": emoji_count,
                    "sentiment": sentiment
                }
            }
            
        except Exception as e:
            logger.error(f"Помилка обробки повідомлення для аналітики: {e}")
            return {"processed": False, "error": str(e)}

    async def _save_message_event(self, chat_id: int, user_id: int, length: int,
                                timestamp: datetime, hour: int, has_emoji: bool,
                                emoji_count: int, word_count: int, sentiment: float):
        """Зберігає подію повідомлення"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO message_events 
                    (chat_id, user_id, message_length, timestamp, hour, 
                     has_emoji, emoji_count, word_count, sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (chat_id, user_id, length, timestamp, hour, 
                     has_emoji, emoji_count, word_count, sentiment))
                
        except Exception as e:
            logger.error(f"Помилка збереження події: {e}")

    def _count_emojis(self, text: str) -> int:
        """Підраховує кількість емодзі в тексті"""
        if not text:
            return 0
        
        emoji_count = 0
        for char in text:
            # Простий спосіб визначення емодзі
            if ord(char) > 0x1F600:  # Базовий діапазон емодзі
                emoji_count += 1
        
        return emoji_count

    async def _analyze_sentiment(self, text: str) -> float:
        """Простий sentiment аналіз"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        # Повертаємо значення від -1 до 1
        return (positive_count - negative_count) / (positive_count + negative_count)

    async def _update_chat_cache(self, chat_id: int, text: str, timestamp: datetime):
        """Оновлює кеш метрик чату"""
        if chat_id not in self.chat_cache:
            self.chat_cache[chat_id] = ChatMetrics(chat_id=chat_id)
        
        metrics = self.chat_cache[chat_id]
        metrics.total_messages += 1
        
        if text:
            # Оновлення середньої довжини
            old_avg = metrics.avg_message_length
            metrics.avg_message_length = (
                (old_avg * (metrics.total_messages - 1) + len(text)) 
                / metrics.total_messages
            )

    async def _update_user_cache(self, user_id: int, username: str, 
                               text: str, timestamp: datetime):
        """Оновлює кеш аналітики користувача"""
        if user_id not in self.user_cache:
            self.user_cache[user_id] = UserAnalytics(
                user_id=user_id, 
                username=username
            )
        
        analytics = self.user_cache[user_id]
        analytics.message_count += 1
        analytics.username = username  # Оновлюємо на випадок зміни
        
        if text:
            # Оновлення середньої довжини
            old_avg = analytics.avg_message_length
            analytics.avg_message_length = (
                (old_avg * (analytics.message_count - 1) + len(text)) 
                / analytics.message_count
            )

    async def get_chat_analytics(self, chat_id: int, 
                               period_days: int = 7) -> Dict[str, Any]:
        """Отримує аналітику чату"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Базові метрики
                cursor = conn.execute("""
                    SELECT COUNT(*) as total_messages,
                           COUNT(DISTINCT user_id) as active_users,
                           AVG(message_length) as avg_length,
                           AVG(sentiment) as avg_sentiment
                    FROM message_events 
                    WHERE chat_id = ? AND timestamp > datetime('now', '-{} days')
                """.format(period_days), (chat_id,))
                
                basic_metrics = cursor.fetchone()
                
                # Активність по годинах
                cursor = conn.execute("""
                    SELECT hour, COUNT(*) as count
                    FROM message_events 
                    WHERE chat_id = ? AND timestamp > datetime('now', '-{} days')
                    GROUP BY hour
                    ORDER BY count DESC
                    LIMIT 1
                """.format(period_days), (chat_id,))
                
                most_active_hour = cursor.fetchone()
                
                # Тренд активності
                cursor = conn.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as count
                    FROM message_events 
                    WHERE chat_id = ? AND timestamp > datetime('now', '-{} days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """.format(period_days), (chat_id,))
                
                daily_activity = cursor.fetchall()
                
                return {
                    "chat_id": chat_id,
                    "period_days": period_days,
                    "total_messages": basic_metrics[0] if basic_metrics else 0,
                    "active_users": basic_metrics[1] if basic_metrics else 0,
                    "avg_message_length": round(basic_metrics[2] or 0, 2),
                    "avg_sentiment": round(basic_metrics[3] or 0, 3),
                    "most_active_hour": most_active_hour[0] if most_active_hour else 12,
                    "daily_activity": daily_activity,
                    "activity_trend": self._calculate_trend(daily_activity)
                }
                
        except Exception as e:
            logger.error(f"Помилка отримання аналітики чату: {e}")
            return {"error": str(e)}

    async def get_user_analytics(self, user_id: int, 
                               period_days: int = 30) -> Dict[str, Any]:
        """Отримує аналітику користувача"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Базові метрики користувача
                cursor = conn.execute("""
                    SELECT COUNT(*) as total_messages,
                           AVG(message_length) as avg_length,
                           AVG(sentiment) as avg_sentiment,
                           SUM(emoji_count) as total_emojis
                    FROM message_events 
                    WHERE user_id = ? AND timestamp > datetime('now', '-{} days')
                """.format(period_days), (user_id,))
                
                basic_metrics = cursor.fetchone()
                
                # Найактивніша година
                cursor = conn.execute("""
                    SELECT hour, COUNT(*) as count
                    FROM message_events 
                    WHERE user_id = ? AND timestamp > datetime('now', '-{} days')
                    GROUP BY hour
                    ORDER BY count DESC
                    LIMIT 1
                """.format(period_days), (user_id,))
                
                most_active_hour = cursor.fetchone()
                
                # Активність по чатах
                cursor = conn.execute("""
                    SELECT chat_id, COUNT(*) as count
                    FROM message_events 
                    WHERE user_id = ? AND timestamp > datetime('now', '-{} days')
                    GROUP BY chat_id
                    ORDER BY count DESC
                    LIMIT 5
                """.format(period_days), (user_id,))
                
                chat_activity = cursor.fetchall()
                
                return {
                    "user_id": user_id,
                    "period_days": period_days,
                    "total_messages": basic_metrics[0] if basic_metrics else 0,
                    "avg_message_length": round(basic_metrics[1] or 0, 2),
                    "avg_sentiment": round(basic_metrics[2] or 0, 3),
                    "total_emojis": basic_metrics[3] if basic_metrics else 0,
                    "most_active_hour": most_active_hour[0] if most_active_hour else 12,
                    "chat_activity": chat_activity,
                    "engagement_score": self._calculate_engagement_score(basic_metrics)
                }
                
        except Exception as e:
            logger.error(f"Помилка отримання аналітики користувача: {e}")
            return {"error": str(e)}

    async def get_global_stats(self, period_days: int = 7) -> Dict[str, Any]:
        """Отримує глобальну статистику"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Загальна статистика
                cursor = conn.execute("""
                    SELECT COUNT(*) as total_messages,
                           COUNT(DISTINCT chat_id) as total_chats,
                           COUNT(DISTINCT user_id) as total_users,
                           AVG(message_length) as avg_length,
                           AVG(sentiment) as avg_sentiment,
                           SUM(emoji_count) as total_emojis
                    FROM message_events 
                    WHERE timestamp > datetime('now', '-{} days')
                """.format(period_days))
                
                global_stats = cursor.fetchone()
                
                # Топ чати по активності
                cursor = conn.execute("""
                    SELECT chat_id, COUNT(*) as count
                    FROM message_events 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY chat_id
                    ORDER BY count DESC
                    LIMIT 10
                """.format(period_days))
                
                top_chats = cursor.fetchall()
                
                # Топ користувачі
                cursor = conn.execute("""
                    SELECT user_id, COUNT(*) as count
                    FROM message_events 
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY user_id
                    ORDER BY count DESC
                    LIMIT 10
                """.format(period_days))
                
                top_users = cursor.fetchall()
                
                return {
                    "period_days": period_days,
                    "total_messages": global_stats[0] if global_stats else 0,
                    "total_chats": global_stats[1] if global_stats else 0,
                    "total_users": global_stats[2] if global_stats else 0,
                    "avg_message_length": round(global_stats[3] or 0, 2),
                    "avg_sentiment": round(global_stats[4] or 0, 3),
                    "total_emojis": global_stats[5] if global_stats else 0,
                    "top_chats": top_chats,
                    "top_users": top_users,
                    "cache_stats": {
                        "cached_chats": len(self.chat_cache),
                        "cached_users": len(self.user_cache)
                    }
                }
                
        except Exception as e:
            logger.error(f"Помилка отримання глобальної статистики: {e}")
            return {"error": str(e)}

    def _calculate_trend(self, daily_data: List[Tuple[str, int]]) -> str:
        """Розраховує тренд активності"""
        if len(daily_data) < 3:
            return "insufficient_data"
        
        # Беремо останні значення
        recent_values = [item[1] for item in daily_data[-3:]]
        
        if len(recent_values) < 2:
            return "stable"
        
        # Простий аналіз тренду
        if recent_values[-1] > recent_values[0] * 1.2:
            return "growing"
        elif recent_values[-1] < recent_values[0] * 0.8:
            return "declining"
        else:
            return "stable"

    def _calculate_engagement_score(self, metrics: Tuple[Any, ...]) -> float:
        """Розраховує рейтинг залученості користувача"""
        if not metrics or not metrics[0]:
            return 0.0
        
        message_count = int(metrics[0]) if metrics[0] else 0
        avg_length = float(metrics[1]) if metrics[1] else 0.0
        avg_sentiment = float(metrics[2]) if metrics[2] else 0.0
        
        # Формула для розрахунку engagement score
        # Враховує кількість повідомлень, їх довжину та позитивність
        base_score = min(message_count / 100.0, 1.0) * 40  # До 40 балів за активність
        length_score = min(avg_length / 50.0, 1.0) * 30    # До 30 балів за довжину
        sentiment_score = max(0, avg_sentiment) * 30       # До 30 балів за позитивність
        
        return round(base_score + length_score + sentiment_score, 2)

    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Очищення старих даних"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Видаляємо старі події
                cursor = conn.execute("""
                    DELETE FROM message_events 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                
                # Очищення кешу
                self.chat_cache.clear()
                self.user_cache.clear()
                
                logger.info(f"Очищено {deleted_count} старих записів аналітики")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Помилка очищення старих даних: {e}")
            return 0

    async def export_analytics(self, output_path: str, 
                             period_days: int = 30) -> bool:
        """Експорт аналітики в JSON"""
        try:
            # Збираємо всі дані
            global_stats = await self.get_global_stats(period_days)
            
            # Отримуємо топ чати
            chat_analytics = []
            if 'top_chats' in global_stats:
                for chat_id, _ in global_stats['top_chats'][:5]:
                    chat_data = await self.get_chat_analytics(chat_id, period_days)
                    chat_analytics.append(chat_data)
            
            # Формуємо звіт
            report = {
                "export_date": datetime.now().isoformat(),
                "period_days": period_days,
                "global_statistics": global_stats,
                "chat_analytics": chat_analytics,
                "metadata": {
                    "version": "3.0",
                    "engine": "AnalyticsEngine"
                }
            }
            
            # Зберігаємо в файл
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Аналітика експортована в {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Помилка експорту аналітики: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Повертає стан аналітичного движка"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM message_events")
                total_events = cursor.fetchone()[0]
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM message_events 
                    WHERE timestamp > datetime('now', '-1 hour')
                """)
                recent_events = cursor.fetchone()[0]
            
            return {
                "status": "healthy",
                "database_connection": True,
                "total_events": total_events,
                "recent_events_1h": recent_events,
                "cache_size": {
                    "chats": len(self.chat_cache),
                    "users": len(self.user_cache)
                }
            }
            
        except Exception as e:
            logger.error(f"Помилка перевірки стану: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "database_connection": False
            }


# Фабрика для створення екземпляру
def create_analytics_engine(db_path: str = "data/analytics.db") -> AnalyticsEngine:
    """Створює екземпляр AnalyticsEngine"""
    return AnalyticsEngine(db_path)
