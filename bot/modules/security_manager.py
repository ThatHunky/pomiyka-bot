"""
Фаза 2: Безпека та стабільність
"""

# 🔐 МОДУЛЬ БЕЗПЕКИ ТА ВАЛІДАЦІЇ
import os
import re
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class SecurityManager:
    """Менеджер безпеки для бота"""
    
    def __init__(self):
        self.failed_attempts: Dict[int, List[datetime]] = {}
        self.blocked_users: Dict[int, datetime] = {}
        self.suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'eval\(',
            r'exec\(',
            r'import\s+os',
            r'subprocess',
            r'__import__'
        ]
        
    def validate_message(self, message_text: str, user_id: int) -> Tuple[bool, str]:
        """
        Валідація повідомлення на безпеку
        
        Returns:
            (is_safe, reason)
        """
        if not message_text:
            return True, "Empty message"
        
        # Перевірка на підозрілі паттерни
        for pattern in self.suspicious_patterns:
            if re.search(pattern, message_text, re.IGNORECASE):
                self._log_security_event(user_id, "suspicious_pattern", pattern)
                return False, f"Підозрілий паттерн: {pattern}"
        
        # Перевірка довжини повідомлення
        if len(message_text) > 10000:
            self._log_security_event(user_id, "message_too_long", len(message_text))
            return False, "Повідомлення занадто довге"
        
        # Перевірка на спам (повторні повідомлення)
        if self._is_spam(message_text, user_id):
            return False, "Підозра на спам"
        
        return True, "Safe"
    
    def _log_security_event(self, user_id: int, event_type: str, details: Any):
        """Логування подій безпеки"""
        logger.warning(f"Security event: {event_type} from user {user_id}: {details}")
        
    def _is_spam(self, message_text: str, user_id: int) -> bool:
        """Перевірка на спам"""
        # Простий алгоритм детекції спаму
        message_hash = hashlib.md5(message_text.encode()).hexdigest()
        
        # Перевіряємо чи не надсилав користувач таке ж повідомлення раніше
        # (тут має бути логіка з БД, поки що заглушка)
        return False
    
    def rate_limit_check(self, user_id: int, action_type: str = "message") -> bool:
        """
        Перевірка rate limiting
        
        Returns:
            True if action is allowed, False if rate limited
        """
        now = datetime.now()
        
        # Перевіряємо чи користувач заблокований
        if user_id in self.blocked_users:
            if now < self.blocked_users[user_id]:
                return False
            else:
                del self.blocked_users[user_id]
        
        # Ініціалізуємо історію спроб
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = []
        
        # Очищуємо старі спроби (старіші за 1 хвилину)
        cutoff_time = now - timedelta(minutes=1)
        self.failed_attempts[user_id] = [
            attempt for attempt in self.failed_attempts[user_id] 
            if attempt > cutoff_time
        ]
        
        # Перевіряємо кількість спроб
        if len(self.failed_attempts[user_id]) >= 10:  # 10 повідомлень за хвилину
            # Блокуємо на 5 хвилин
            self.blocked_users[user_id] = now + timedelta(minutes=5)
            self._log_security_event(user_id, "rate_limited", len(self.failed_attempts[user_id]))
            return False
        
        # Додаємо поточну спробу
        self.failed_attempts[user_id].append(now)
        return True
    
    def validate_admin_command(self, user_id: int, command: str) -> bool:
        """Валідація команд адміністратора"""
        try:
            admin_id = int(os.getenv('ADMIN_ID', '0'))
            if admin_id == 0:
                logger.warning("ADMIN_ID не налаштовано")
                return False
            
            if user_id != admin_id:
                self._log_security_event(user_id, "unauthorized_admin_command", command)
                return False
            
            return True
        except ValueError:
            logger.error("Неправильний формат ADMIN_ID")
            return False
    
    def sanitize_input(self, text: str) -> str:
        """Санітизація користувацького вводу"""
        if not text:
            return ""
        
        # Видаляємо потенційно небезпечні символи
        sanitized = re.sub(r'[<>"\']', '', text)
        
        # Обмежуємо довжину
        if len(sanitized) > 1000:
            sanitized = sanitized[:1000] + "..."
        
        return sanitized.strip()
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Отримання статистики безпеки"""
        now = datetime.now()
        active_blocks = sum(
            1 for block_until in self.blocked_users.values() 
            if block_until > now
        )
        
        return {
            'blocked_users_count': active_blocks,
            'total_users_monitored': len(self.failed_attempts),
            'security_events_today': self._count_todays_events()
        }
    
    def _count_todays_events(self) -> int:
        """Підрахунок подій безпеки за сьогодні"""
        # Тут має бути логіка підрахунку з логів
        return 0

class InputValidator:
    """Валідатор користувацького вводу"""
    
    @staticmethod
    def validate_chat_id(chat_id: Any) -> bool:
        """Валідація ID чату"""
        try:
            chat_id_int = int(chat_id)
            return -1000000000000 <= chat_id_int <= 1000000000000
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_user_id(user_id: Any) -> bool:
        """Валідація ID користувача"""
        try:
            user_id_int = int(user_id)
            return 1 <= user_id_int <= 10000000000
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Валідація імені файлу"""
        if not filename or len(filename) > 255:
            return False
        
        # Перевіряємо на небезпечні символи
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return not any(char in filename for char in dangerous_chars)
    
    @staticmethod
    def validate_json_data(data: str, max_size: int = 10000) -> Tuple[bool, Optional[Dict]]:
        """Валідація JSON даних"""
        if len(data) > max_size:
            return False, None
        
        try:
            parsed = json.loads(data)
            return True, parsed
        except json.JSONDecodeError:
            return False, None

class ErrorHandler:
    """Централізований обробник помилок"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.last_errors: List[Tuple[datetime, str, str]] = []
    
    def handle_error(self, error: Exception, context: str = "") -> str:
        """
        Обробка помилки з логуванням та збором статистики
        
        Returns:
            User-friendly error message
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        # Збільшуємо лічильник помилок
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Додаємо до історії помилок
        self.last_errors.append((datetime.now(), error_type, error_message))
        
        # Зберігаємо тільки останні 100 помилок
        if len(self.last_errors) > 100:
            self.last_errors = self.last_errors[-100:]
        
        # Логуємо помилку
        logger.error(f"Error in {context}: {error_type}: {error_message}", exc_info=True)
        
        # Повертаємо дружелюбне повідомлення для користувача
        user_messages = {
            'ConnectionError': 'Тимчасові проблеми з підключенням. Спробуйте пізніше.',
            'TimeoutError': 'Операція зайняла занадто багато часу. Спробуйте ще раз.',
            'ValueError': 'Некоректні дані. Перевірте введену інформацію.',
            'PermissionError': 'Недостатньо прав для виконання операції.',
            'FileNotFoundError': 'Файл не знайдено.',
            'KeyError': 'Відсутні необхідні дані.',
        }
        
        return user_messages.get(error_type, 'Виникла технічна помилка. Спробуйте пізніше.')
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Отримання статистики помилок"""
        recent_errors = [
            error for timestamp, _, _ in self.last_errors
            if timestamp > datetime.now() - timedelta(hours=24)
        ]
        
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_types': dict(self.error_counts),
            'recent_errors_24h': len(recent_errors),
            'last_error': self.last_errors[-1] if self.last_errors else None
        }

# Глобальні екземпляри
security_manager = SecurityManager()
input_validator = InputValidator()
error_handler = ErrorHandler()

# Функції для зворотної сумісності
def validate_message_security(message_text: str, user_id: int) -> bool:
    """Швидка перевірка безпеки повідомлення"""
    is_safe, _ = security_manager.validate_message(message_text, user_id)
    return is_safe

def check_rate_limit(user_id: int) -> bool:
    """Швидка перевірка rate limiting"""
    return security_manager.rate_limit_check(user_id)

def handle_bot_error(error: Exception, context: str = "") -> str:
    """Швидка обробка помилки"""
    return error_handler.handle_error(error, context)
