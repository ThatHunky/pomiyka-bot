# Модуль валідації конфігурації та безпеки
import os
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ConfigValidationError(Exception):
    """Помилка валідації конфігурації"""
    pass

class ConfigValidator:
    """Валідатор конфігурації бота з перевірками безпеки"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Повна валідація конфігурації"""
        self.errors.clear()
        self.warnings.clear()
        
        # Основні перевірки
        self._validate_required_env_vars()
        self._validate_api_tokens()
        self._validate_paths()
        self._validate_numeric_configs()
        self._validate_security_settings()
        self._validate_bot_limits()
        
        # Перевірки продуктивності
        self._validate_performance_settings()
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors.copy(), self.warnings.copy()
    
    def _validate_required_env_vars(self):
        """Перевіряє наявність обов'язкових змінних середовища"""
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "GEMINI_API_KEY",
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Відсутня обов'язкова змінна середовища: {var}")
            elif len(value.strip()) == 0:
                self.errors.append(f"Порожнє значення для змінної: {var}")
    
    def _validate_api_tokens(self):
        """Валідація формату API токенів"""
        # Telegram Bot Token format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if telegram_token:
            if not re.match(r'^\d{8,10}:[A-Za-z0-9_-]{35}$', telegram_token):
                self.errors.append("Неправильний формат TELEGRAM_BOT_TOKEN")
        
        # Gemini API Key format check (basic)
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            if len(gemini_key) < 20:
                self.warnings.append("GEMINI_API_KEY здається занадто коротким")
            if ' ' in gemini_key:
                self.errors.append("GEMINI_API_KEY містить пробіли")
    
    def _validate_paths(self):
        """Перевірка шляхів до файлів та директорій"""
        data_dir = os.getenv("BOT_DATA_DIR", "data")
        
        # Створюємо директорію якщо не існує
        try:
            Path(data_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.errors.append(f"Не вдалося створити директорію {data_dir}: {e}")
        
        # Перевіряємо права доступу
        if not os.access(data_dir, os.W_OK):
            self.errors.append(f"Немає прав на запис у директорію: {data_dir}")
    
    def _validate_numeric_configs(self):
        """Валідація числових конфігурацій"""
        numeric_configs = {
            "BOT_CONTEXT_LIMIT": (10, 10000, "Ліміт контексту"),
            "BOT_MAX_CONTEXT_SIZE": (1000, 100000, "Максимальний розмір контексту (ЗАСТАРІЛИЙ)"),
            "BOT_MAX_CONTEXT_TOKENS": (10000, 1000000, "Максимальна кількість токенів контексту"),
            "BOT_CONTEXT_CHAR_ESTIMATE": (100000, 5000000, "Оцінка символів для контексту"),
            "BOT_MIN_SILENCE_MINUTES": (1, 120, "Мінімальна тиша"),
            "BOT_MAX_REPLIES_PER_HOUR": (1, 20, "Максимум відповідей на годину"),
            "BOT_SPAM_THRESHOLD": (3, 50, "Поріг спаму"),
            "BOT_SPAM_TIMEOUT": (60, 3600, "Таймаут спаму"),
            "ADMIN_ID": (1, 9999999999, "ID адміністратора"),
        }
        
        for var_name, (min_val, max_val, description) in numeric_configs.items():
            value_str = os.getenv(var_name)
            if value_str:
                try:
                    value = int(value_str)
                    if not (min_val <= value <= max_val):
                        self.errors.append(
                            f"{description} ({var_name}) має бути між {min_val} та {max_val}, "
                            f"отримано: {value}"
                        )
                except ValueError:
                    self.errors.append(f"{description} ({var_name}) має бути числом, отримано: {value_str}")
    
    def _validate_security_settings(self):
        """Перевірка налаштувань безпеки"""
        # Перевірка чи не використовуються небезпечні налаштування
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if "test" in bot_token.lower() or "demo" in bot_token.lower():
            self.warnings.append("Використовується тестовий токен Telegram")
        
        # Перевірка debug режиму
        debug_mode = os.getenv("DEBUG", "false").lower()
        if debug_mode == "true":
            self.warnings.append("Увімкнено DEBUG режим - вимкніть у продакшні")
        
        # Перевірка admin ID
        admin_id = os.getenv("ADMIN_ID")
        if not admin_id:
            self.warnings.append("Не вказано ADMIN_ID - адміністративні команди будуть недоступні")
    
    def _validate_bot_limits(self):
        """Валідація лімітів бота"""
        # Перевірка співвідношення лімітів
        try:
            context_limit = int(os.getenv("BOT_CONTEXT_LIMIT", "1000"))
            max_context_size = int(os.getenv("BOT_MAX_CONTEXT_SIZE", "10000"))
            max_context_tokens = int(os.getenv("BOT_MAX_CONTEXT_TOKENS", "800000"))
            
            if context_limit > max_context_size:
                self.warnings.append(
                    "BOT_CONTEXT_LIMIT більше ніж BOT_MAX_CONTEXT_SIZE - може призвести до обрізання"
                )
            
            # Перевірка токенів (новий параметр)
            if max_context_tokens > 1000000:
                self.warnings.append(
                    "BOT_MAX_CONTEXT_TOKENS більше ніж 1M (ліміт Gemini 2.5 Flash) - може призвести до помилок"
                )
            
            # Перевірка коефіцієнта токенів
            tokens_per_char = float(os.getenv("BOT_TOKENS_PER_CHAR", "0.4"))
            if tokens_per_char < 0.1 or tokens_per_char > 1.0:
                self.warnings.append(
                    f"BOT_TOKENS_PER_CHAR ({tokens_per_char}) виглядає нереалістичним (рекомендовано 0.3-0.5)"
                )
        except ValueError:
            pass  # Вже перевірено в numeric_configs
        
        # Перевірка шансів відповідей
        try:
            random_chance = float(os.getenv("BOT_RANDOM_REPLY_CHANCE", "0.2"))
            smart_chance = float(os.getenv("BOT_SMART_REPLY_CHANCE", "0.03"))
            
            if random_chance > 0.5:
                self.warnings.append("BOT_RANDOM_REPLY_CHANCE занадто високий (>50%) - може спамити")
            
            if smart_chance > 0.1:
                self.warnings.append("BOT_SMART_REPLY_CHANCE занадто високий (>10%) - може спамити")
                
        except ValueError:
            self.errors.append("Неправильний формат для шансів відповідей (мають бути числами)")
    
    def _validate_performance_settings(self):
        """Перевірка налаштувань продуктивності"""
        # Gemini model validation
        gemini_model = os.getenv("GEMINI_MODEL", "")
        recommended_models = [
            "gemini-2.5-flash", "gemini-2.0-flash", 
            "gemini-1.5-flash", "gemini-1.5-pro"
        ]
        
        if gemini_model and gemini_model not in recommended_models:
            self.warnings.append(
                f"Модель Gemini '{gemini_model}' не у списку рекомендованих. "
                f"Рекомендовані: {', '.join(recommended_models)}"
            )
        
        # Cache settings
        enable_cache = os.getenv("GEMINI_ENABLE_CACHE", "true").lower()
        if enable_cache == "false":
            self.warnings.append("Кешування Gemini вимкнено - може зменшити продуктивність")
        
        # Database optimization
        if not os.getenv("USE_ASYNC_DB"):
            self.warnings.append("Рекомендується увімкнути USE_ASYNC_DB=true для кращої продуктивності")

def validate_startup_config() -> bool:
    """Валідує конфігурацію при старті додатка"""
    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_all()
    
    # Логуємо результати
    if errors:
        logger.error("Критичні помилки конфігурації:")
        for error in errors:
            logger.error(f"  ❌ {error}")
    
    if warnings:
        logger.warning("Попередження конфігурації:")
        for warning in warnings:
            logger.warning(f"  ⚠️ {warning}")
    
    if is_valid:
        logger.info("✅ Конфігурація валідна")
    else:
        logger.error("❌ Конфігурація містить критичні помилки")
    
    return is_valid

def get_config_recommendations() -> Dict[str, Any]:
    """Повертає рекомендації для оптимізації конфігурації"""
    recommendations = {
        "performance": [
            "Увімкніть USE_ASYNC_DB=true для асинхронної бази даних",
            "Використовуйте GEMINI_ENABLE_CACHE=true для кешування",
            "Встановіть BOT_CONTEXT_LIMIT=1000 для оптимального балансу",
        ],
        "security": [
            "Встановіть сильний ADMIN_ID з вашим Telegram ID",
            "Використовуйте унікальні API ключі для кожного середовища",
            "Вимкніть DEBUG=false у продакшні",
        ],
        "reliability": [
            "Встановіть BOT_MAX_REPLIES_PER_HOUR=3 для запобігання спаму",
            "Використовуйте BOT_IGNORE_OLD_MESSAGES=true",
            "Встановіть BOT_SPAM_THRESHOLD=5 для захисту від зловживань",
        ]
    }
    
    return recommendations

def create_sample_env_file(filepath: str = ".env.sample"):
    """Створює приклад файлу .env з коментарями"""
    sample_content = '''# === ОСНОВНІ НАЛАШТУВАННЯ ===
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
GEMINI_API_KEY=your_gemini_api_key_here
ADMIN_ID=392817811

# === НАЛАШТУВАННЯ БОТА ===
BOT_PERSONA_NAME=Гряг
BOT_PERSONA_DESC=Дружелюбний та розумний помічник з легким гумором!
BOT_CONTEXT_LIMIT=1000
BOT_MAX_CONTEXT_SIZE=10000

# === ПЕРСОНАЛЬНІСТЬ ===
BOT_RANDOM_REPLY_CHANCE=0.20
BOT_SMART_REPLY_CHANCE=0.03
BOT_MIN_SILENCE_MINUTES=30
BOT_MAX_REPLIES_PER_HOUR=2

# === СПОНТАННА АКТИВНІСТЬ ===
BOT_AUTONOMOUS_MODE=true
BOT_SPONTANEOUS_CHANCE=0.005
BOT_SPONTANEOUS_MIN_PAUSE=40

# === АНТИ-СПАМ ===
BOT_SPAM_THRESHOLD=6
BOT_SPAM_TIMEOUT=180
BOT_SPAM_REPLY_CHANCE=0.2

# === РЕАКЦІЇ ===
BOT_REACTION_CHANCE=0.05
BOT_REACTION_ON_MENTIONS=true

# === БЕЗПЕКА ===
BOT_IGNORE_OLD_MESSAGES=true
BOT_MAX_MESSAGE_AGE_MINUTES=10

# === ПРОДУКТИВНІСТЬ ===
USE_ASYNC_DB=true
GEMINI_ENABLE_CACHE=true
GEMINI_MODEL=gemini-2.5-flash
BOT_DATA_DIR=data

# === РОЗРОБКА ===
DEBUG=false
LOG_LEVEL=INFO
'''
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        logger.info(f"Створено приклад файлу конфігурації: {filepath}")
        return True
    except Exception as e:
        logger.error(f"Помилка створення файлу {filepath}: {e}")
        return False

# Функції для швидкої перевірки
def quick_validate() -> bool:
    """Швидка валідація критичних налаштувань"""
    required = ["TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY"]
    for var in required:
        if not os.getenv(var):
            logger.error(f"Відсутня критична змінна: {var}")
            return False
    return True

def check_env_file_exists() -> bool:
    """Перевіряє чи існує файл .env"""
    return os.path.exists(".env")

if __name__ == "__main__":
    # Тестування валідатора
    validate_startup_config()
    
    if not check_env_file_exists():
        print("Файл .env не знайдено. Створюємо .env.sample...")
        create_sample_env_file()
