# Модуль для інтеграції з Gemini (конфігуруємо модель)
# ОНОВЛЕНО: Тепер використовує покращений Gemini API клієнт

import logging
from aiogram.types import Message
from typing import Optional, Dict, Any, Callable

# Імпортуємо покращений API клієнт
from .gemini_enhanced import (
    process_message as enhanced_process_message,
    get_api_stats,
    clear_cache,
    cleanup,
    GeminiAPIClient
)

# Обгортка для сумісності зі старим кодом
async def process_message(message: Message, tone_instruction: Optional[str] = None) -> str:
    """
    Обробляє повідомлення через покращений Gemini API з урахуванням контексту та тону.
    
    Args:
        message: Повідомлення для обробки (може бути FakeMessage з додатковими даними)
        tone_instruction: Додаткова інструкція для тону відповіді
        
    Returns:
        Відповідь від Gemini
    """
    try:
        # Передаємо виклик до покращеного модуля
        return await enhanced_process_message(message, tone_instruction)
        
    except Exception as e:
        logging.error(f"Помилка в process_message: {e}")
        return "Вибачте, сталася помилка при обробці повідомлення."

# Застарілі функції для сумісності
async def _make_gemini_request(prompt: str) -> str:
    """Застаріла функція. Використовуйте покращений API."""
    logging.warning("Використання застарілої функції _make_gemini_request. Переходьте на покращений API.")
    # Можемо створити простий запит через новий API
    from .gemini_enhanced import get_client
    client = await get_client()
    return await client.generate_content(prompt)

async def safe_api_call(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Застаріла функція. Використовуйте покращений API."""
    from .gemini_enhanced import safe_api_call as enhanced_safe_api_call
    return await enhanced_safe_api_call(func, *args, **kwargs)

# Додаткові функції для адміністрування
async def get_gemini_stats() -> Dict[str, Any]:
    """Повертає статистику використання Gemini API."""
    return await get_api_stats()

async def clear_gemini_cache():
    """Очищає кеш Gemini API."""
    await clear_cache()
    logging.info("Кеш Gemini API очищено")

async def shutdown_gemini():
    """Коректно завершує роботу з Gemini API."""
    await cleanup()
    logging.info("Gemini API коректно завершено")

# Функції для роботи з покращеними можливостями
async def generate_structured_response(prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """Генерує структуровану JSON відповідь."""
    from .gemini_enhanced import generate_json_response
    return await generate_json_response(prompt, schema)

async def create_custom_client(model: Optional[str] = None, 
                               temperature: Optional[float] = None,
                               max_tokens: Optional[int] = None,
                               enable_thinking: Optional[bool] = None) -> GeminiAPIClient:
    """Створює кастомний клієнт з вказаними параметрами."""
    from .gemini_enhanced import GEMINI_MODEL
    from bot.bot_config import GEMINI_MODEL as DEFAULT_MODEL
    
    model = model or DEFAULT_MODEL or GEMINI_MODEL
    client = GeminiAPIClient(model=model)
    
    # Можна додати кастомні налаштування
    if temperature is not None or max_tokens is not None or enable_thinking is not None:
        logging.info(f"Створено кастомний Gemini клієнт з моделлю {model}")
    
    return client

# Експорт для зручності
__all__ = [
    'process_message',
    'get_gemini_stats', 
    'clear_gemini_cache',
    'shutdown_gemini',
    'generate_structured_response',
    'create_custom_client',
    'safe_api_call',
    '_make_gemini_request'  # застаріла
]
