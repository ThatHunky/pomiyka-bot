import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Базові шляхи для персистентних даних
DATA_DIR: str = os.getenv("BOT_DATA_DIR", "data")

# Конфіг для особистості бота та лімітів
PERSONA: Dict[str, Any] = {
    "name": os.getenv("BOT_PERSONA_NAME", "Гряг"),
    "description": os.getenv("BOT_PERSONA_DESC", "Зачекайте, я реальний?!"),
    "context_limit": int(os.getenv("BOT_CONTEXT_LIMIT", "1000")),
    "reply_timeout": int(os.getenv("BOT_REPLY_TIMEOUT", "10")),
    "admin_id": int(os.getenv("ADMIN_ID", "392817811")),
    "random_reply_chance": float(os.getenv("BOT_RANDOM_REPLY_CHANCE", "0.3")),
    "max_context_size": int(os.getenv("BOT_MAX_CONTEXT_SIZE", "10000")),
    # Анти-спам
    "smart_reply_chance": float(os.getenv("BOT_SMART_REPLY_CHANCE", "0.05")),
    "min_silence_minutes": int(os.getenv("BOT_MIN_SILENCE_MINUTES", "20")),
    "max_replies_per_hour": int(os.getenv("BOT_MAX_REPLIES_PER_HOUR", "2")),
    "trigger_keywords": os.getenv("BOT_TRIGGER_KEYWORDS", "гряг,@gryag_bot,грягік,бот").split(","),
    # Автономність
    "autonomous_mode": os.getenv("BOT_AUTONOMOUS_MODE", "true").lower() == "true",
    "spontaneous_chance": float(os.getenv("BOT_SPONTANEOUS_CHANCE", "0.01")),
    "spontaneous_min_pause": int(os.getenv("BOT_SPONTANEOUS_MIN_PAUSE", "30")),  # хвилин між спонтанними
    # Агресивний троттлінг
    "spam_threshold": int(os.getenv("BOT_SPAM_THRESHOLD", "5")),  # повідомлень за хвилину
    "spam_timeout": int(os.getenv("BOT_SPAM_TIMEOUT", "300")),   # секунд ігнорування
    "spam_replies": os.getenv("BOT_SPAM_REPLIES", "тіха блять, хохли;не спамте;заткніться на хвилинку").split(";"),
    "spam_reply_chance": float(os.getenv("BOT_SPAM_REPLY_CHANCE", "0.3")),
    # Реакції
    "reaction_chance": float(os.getenv("BOT_REACTION_CHANCE", "0.05")),
    "reaction_on_mentions": os.getenv("BOT_REACTION_ON_MENTIONS", "true").lower() == "true",
    # Історія чату
    "auto_scan_history": os.getenv("BOT_AUTO_SCAN_HISTORY", "true").lower() == "true",
    "max_history_scan": int(os.getenv("BOT_MAX_HISTORY_SCAN", "500")),
    # Ігнорування старих повідомлень
    "ignore_old_messages": os.getenv("BOT_IGNORE_OLD_MESSAGES", "true").lower() == "true",
    "max_message_age_minutes": int(os.getenv("BOT_MAX_MESSAGE_AGE_MINUTES", "10")),  # хвилин
    # Rate limiting для запобігання flood control
    "rate_limit_per_chat": int(os.getenv("BOT_RATE_LIMIT_PER_CHAT", "3")),  # повідомлень на хвилину на чат
    "global_rate_limit": int(os.getenv("BOT_GLOBAL_RATE_LIMIT", "20")),  # повідомлень на хвилину глобально
    "error_reply_chance": float(os.getenv("BOT_ERROR_REPLY_CHANCE", "0.1"))  # шанс відповіді при помилці
}

# Gemini налаштування
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Шляхи до файлів даних
DB_PATH: str = os.path.join(DATA_DIR, "context.db")
MEDIA_MAP_PATH: str = os.path.join(DATA_DIR, "media_map.json")
CHAT_STATE_PATH: str = os.path.join(DATA_DIR, "chat_states.json")
