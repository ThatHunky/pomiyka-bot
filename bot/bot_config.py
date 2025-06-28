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
    "random_reply_chance": float(os.getenv("BOT_RANDOM_REPLY_CHANCE", "0.25")),  # Зменшено з 0.35 до 0.25 для менш агресивної поведінки
    "max_context_size": int(os.getenv("BOT_MAX_CONTEXT_SIZE", "15000")),  # Збільшено з 10000 до 15000
    # Нові налаштування для токенів Gemini 2.5 Flash (1M токенів)
    "max_context_tokens": int(os.getenv("BOT_MAX_CONTEXT_TOKENS", "800000")),  # 80% від 1M токенів
    "context_char_estimate": int(os.getenv("BOT_CONTEXT_CHAR_ESTIMATE", "2000000")),  # ~2M символів безпечно
    "tokens_per_char_ukrainian": float(os.getenv("BOT_TOKENS_PER_CHAR", "0.4")),  # 1 токен ≈ 2.5 символа для української
    # Анти-спам (зменшено агресивність)
    "smart_reply_chance": float(os.getenv("BOT_SMART_REPLY_CHANCE", "0.20")),  # Збільшено з 0.15 до 0.20
    "min_silence_minutes": int(os.getenv("BOT_MIN_SILENCE_MINUTES", "12")),  # Зменшено з 15 до 12
    "max_replies_per_hour": int(os.getenv("BOT_MAX_REPLIES_PER_HOUR", "6")),  # Збільшено з 5 до 6
    "trigger_keywords": os.getenv("BOT_TRIGGER_KEYWORDS", "гряг,@gryag_bot,грягік,бот").split(","),
    # Автономність (зменшено активність)
    "autonomous_mode": os.getenv("BOT_AUTONOMOUS_MODE", "true").lower() == "true",
    "spontaneous_chance": float(os.getenv("BOT_SPONTANEOUS_CHANCE", "0.005")),  # зменшено з 0.008
    "spontaneous_min_pause": int(os.getenv("BOT_SPONTANEOUS_MIN_PAUSE", "40")),  # збільшено з 35
    # Агресивний троттлінг - ЗМЕНШЕНО для більшої активності
    "spam_threshold": int(os.getenv("BOT_SPAM_THRESHOLD", "8")),  # Збільшено з 6 до 8
    "spam_timeout": int(os.getenv("BOT_SPAM_TIMEOUT", "120")),   # Зменшено з 180 до 120
    "spam_replies": os.getenv("BOT_SPAM_REPLIES", "не спамте;дайте подихати;зачекайте трохи;спокійніше").split(";"),  # м'якші фрази
    "spam_reply_chance": float(os.getenv("BOT_SPAM_REPLY_CHANCE", "0.15")),  # Зменшено з 0.2 до 0.15
    # Реакції - ЗБІЛЬШЕНО активність
    "reaction_chance": float(os.getenv("BOT_REACTION_CHANCE", "0.12")),  # Збільшено з 0.05 до 0.12
    "reaction_on_mentions": os.getenv("BOT_REACTION_ON_MENTIONS", "true").lower() == "true",
    # Історія чату
    "auto_scan_history": os.getenv("BOT_AUTO_SCAN_HISTORY", "true").lower() == "true",
    "max_history_scan": int(os.getenv("BOT_MAX_HISTORY_SCAN", "500")),
    # Ігнорування старих повідомлень
    "ignore_old_messages": os.getenv("BOT_IGNORE_OLD_MESSAGES", "true").lower() == "true",
    "max_message_age_minutes": int(os.getenv("BOT_MAX_MESSAGE_AGE_MINUTES", "10")),  # хвилин
    # Rate limiting для запобігання flood control - ЗМЕНШЕНО обмеження
    "rate_limit_per_chat": int(os.getenv("BOT_RATE_LIMIT_PER_CHAT", "6")),  # Збільшено з 3 до 6
    "global_rate_limit": int(os.getenv("BOT_GLOBAL_RATE_LIMIT", "30")),  # Збільшено з 20 до 30
    "error_reply_chance": float(os.getenv("BOT_ERROR_REPLY_CHANCE", "0.15")),  # Збільшено з 0.1 до 0.15
    # Локальний аналізатор
    "local_analysis_enabled": os.getenv("BOT_LOCAL_ANALYSIS_ENABLED", "true").lower() == "true",
    "local_model_type": os.getenv("BOT_LOCAL_MODEL_TYPE", "sentence_transformers"),  # sentence_transformers, ollama
    "analysis_batch_size": int(os.getenv("BOT_ANALYSIS_BATCH_SIZE", "5")),  # оптимально для i5-6500
    "analysis_cache_hours": int(os.getenv("BOT_ANALYSIS_CACHE_HOURS", "24")),  # час життя кешу
    "enhanced_context_enabled": os.getenv("BOT_ENHANCED_CONTEXT_ENABLED", "true").lower() == "true"
}

# Gemini налаштування
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Веб-інтерфейс
WEB_PORT: int = int(os.getenv("BOT_WEB_PORT", "1488"))

# Шляхи до файлів даних
DB_PATH: str = os.path.join(DATA_DIR, "context.db")
MEDIA_MAP_PATH: str = os.path.join(DATA_DIR, "media_map.json")
CHAT_STATE_PATH: str = os.path.join(DATA_DIR, "chat_states.json")
LOCAL_ANALYZER_DB_PATH: str = os.path.join(DATA_DIR, "analysis_cache.db")
