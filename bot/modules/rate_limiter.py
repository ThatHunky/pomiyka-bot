"""
Модуль для rate limiting та запобігання flood control
"""
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, DefaultDict
import logging

class RateLimiter:
    def __init__(self):
        # Трекінг повідомлень по чатах (chat_id -> timestamps)
        self.chat_messages: DefaultDict[int, deque] = defaultdict(deque)
        # Глобальний трекінг повідомлень
        self.global_messages: deque = deque()
        # Трекінг помилок по чатах
        self.chat_errors: DefaultDict[int, deque] = defaultdict(deque)
        
    def _clean_old_timestamps(self, timestamps: deque, window_minutes: int = 1):
        """Очищає старі timestamps за вказаний період"""
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        while timestamps and timestamps[0] < cutoff:
            timestamps.popleft()
    
    def can_send_to_chat(self, chat_id: int, limit_per_minute: int = 6) -> bool:  # Збільшено з 3 до 6
        """Перевіряє чи можна відправити повідомлення в конкретний чат"""
        now = datetime.now()
        chat_timestamps = self.chat_messages[chat_id]
        
        # Очищаємо старі timestamps
        self._clean_old_timestamps(chat_timestamps)
        
        # Перевіряємо ліміт
        if len(chat_timestamps) >= limit_per_minute:
            logging.warning(f"Rate limit для чату {chat_id}: {len(chat_timestamps)}/{limit_per_minute}")
            return False
        
        # Додаємо поточний timestamp
        chat_timestamps.append(now)
        return True
    
    def can_send_globally(self, global_limit_per_minute: int = 30) -> bool:  # Збільшено з 20 до 30
        """Перевіряє глобальний ліміт повідомлень"""
        now = datetime.now()
        
        # Очищаємо старі timestamps
        self._clean_old_timestamps(self.global_messages)
        
        # Перевіряємо ліміт
        if len(self.global_messages) >= global_limit_per_minute:
            logging.warning(f"Глобальний rate limit: {len(self.global_messages)}/{global_limit_per_minute}")
            return False
        
        # Додаємо поточний timestamp
        self.global_messages.append(now)
        return True
    
    def can_send_message(self, chat_id: int, chat_limit: int = 3, global_limit: int = 20) -> bool:
        """Комплексна перевірка rate limiting"""
        return (self.can_send_to_chat(chat_id, chat_limit) and 
                self.can_send_globally(global_limit))
    
    def record_error(self, chat_id: int):
        """Записує помилку для чату"""
        now = datetime.now()
        self.chat_errors[chat_id].append(now)
        
        # Очищаємо старі помилки (за 5 хвилин)
        cutoff = now - timedelta(minutes=5)
        while self.chat_errors[chat_id] and self.chat_errors[chat_id][0] < cutoff:
            self.chat_errors[chat_id].popleft()
    
    def get_error_count(self, chat_id: int, window_minutes: int = 5) -> int:
        """Отримує кількість помилок за вказаний період"""
        self._clean_old_timestamps(self.chat_errors[chat_id], window_minutes)
        return len(self.chat_errors[chat_id])
    
    def should_suppress_errors(self, chat_id: int, max_errors: int = 3) -> bool:
        """Перевіряє чи потрібно придушити повідомлення про помилки"""
        return self.get_error_count(chat_id) >= max_errors

# Глобальний instance
rate_limiter = RateLimiter()
