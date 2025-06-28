import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Базові шляхи для персистентних даних
DATA_DIR: str = os.getenv("BOT_DATA_DIR", "data")

# Конфіг для особистості бота та лімітів
PERSONA: Dict[str, Any] = {
    "name": os.getenv("BOT_PERSONA_NAME", "Гряг"),
    "description": os.getenv("BOT_PERSONA_DESC", "Дружелюбний та розумний помічник з легким гумором!"),
    "context_limit": int(os.getenv("BOT_CONTEXT_LIMIT", "1000")),
    "reply_timeout": int(os.getenv("BOT_REPLY_TIMEOUT", "10")),
    "admin_id": int(os.getenv("ADMIN_ID", "392817811")),
    "random_reply_chance": float(os.getenv("BOT_RANDOM_REPLY_CHANCE", "0.20")),  # зменшено з 0.25
    "max_context_size": int(os.getenv("BOT_MAX_CONTEXT_SIZE", "10000")),
    # Анти-спам (зменшено агресивність)
    "smart_reply_chance": float(os.getenv("BOT_SMART_REPLY_CHANCE", "0.03")),  # зменшено з 0.04
    "min_silence_minutes": int(os.getenv("BOT_MIN_SILENCE_MINUTES", "30")),  # збільшено з 25
    "max_replies_per_hour": int(os.getenv("BOT_MAX_REPLIES_PER_HOUR", "2")),
    "trigger_keywords": os.getenv("BOT_TRIGGER_KEYWORDS", "гряг,@gryag_bot,грягік,бот").split(","),
    # Автономність (зменшено активність)
    "autonomous_mode": os.getenv("BOT_AUTONOMOUS_MODE", "true").lower() == "true",
    "spontaneous_chance": float(os.getenv("BOT_SPONTANEOUS_CHANCE", "0.005")),  # зменшено з 0.008
    "spontaneous_min_pause": int(os.getenv("BOT_SPONTANEOUS_MIN_PAUSE", "40")),  # збільшено з 35
    # Агресивний троттлінг (м'якші реакції)
    "spam_threshold": int(os.getenv("BOT_SPAM_THRESHOLD", "6")),  # збільшено з 5
    "spam_timeout": int(os.getenv("BOT_SPAM_TIMEOUT", "180")),   # зменшено з 300
    "spam_replies": os.getenv("BOT_SPAM_REPLIES", "не спамте;дайте подихати;зачекайте трохи;спокійніше").split(";"),  # м'якші фрази
    "spam_reply_chance": float(os.getenv("BOT_SPAM_REPLY_CHANCE", "0.2")),  # зменшено з 0.3
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
    "error_reply_chance": float(os.getenv("BOT_ERROR_REPLY_CHANCE", "0.1")),  # шанс відповіді при помилці
    # Локальний аналізатор
    "local_analysis_enabled": os.getenv("BOT_LOCAL_ANALYSIS_ENABLED", "true").lower() == "true",
    "local_model_type": os.getenv("BOT_LOCAL_MODEL_TYPE", "sentence_transformers"),  # sentence_transformers, ollama
    "analysis_batch_size": int(os.getenv("BOT_ANALYSIS_BATCH_SIZE", "5")),  # оптимально для i5-6500
    "analysis_cache_hours": int(os.getenv("BOT_ANALYSIS_CACHE_HOURS", "24")),  # час життя кешу
    "enhanced_context_enabled": os.getenv("BOT_ENHANCED_CONTEXT_ENABLED", "true").lower() == "true"
}

# Gemini налаштування
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Шляхи до файлів даних
DB_PATH: str = os.path.join(DATA_DIR, "context.db")
MEDIA_MAP_PATH: str = os.path.join(DATA_DIR, "media_map.json")
CHAT_STATE_PATH: str = os.path.join(DATA_DIR, "chat_states.json")
LOCAL_ANALYZER_DB_PATH: str = os.path.join(DATA_DIR, "analysis_cache.db")
