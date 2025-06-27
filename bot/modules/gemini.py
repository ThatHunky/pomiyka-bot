# Модуль для інтеграції з Gemini (конфігуруємо модель)
import aiohttp
import asyncio
import logging
from aiogram.types import Message
from . import context
import os
from dotenv import load_dotenv
from typing import Optional, Callable, Any, List
from bot.bot_config import GEMINI_MODEL

load_dotenv()

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY не знайдено в змінних середовища")

async def process_message(message: Message, tone_instruction: Optional[str] = None) -> str:
    """
    Обробляє повідомлення через Gemini API з урахуванням контексту та тону.
    
    Args:
        message: Повідомлення для обробки
        tone_instruction: Додаткова інструкція для тону відповіді
        
    Returns:
        Відповідь від Gemini
    """
    try:
        from bot.bot_config import PERSONA
        chat_context = context.get_context(message.chat.id)
        
        # Додаємо дружню інструкцію та динамічний опис обстановки
        last_msgs = [m.get('text', '') for m in chat_context[-5:] if m.get('text')]
        mood_hint = _analyze_chat_mood(last_msgs)
        
        # Базова персона
        persona_prompt = _build_persona_prompt(mood_hint, tone_instruction)
        
        # Формуємо історію діалогу
        history = [f"{m['user']}: {m['text']}" for m in chat_context[-PERSONA['context_limit']:] if m.get('text')]
        
        # Додаємо поточне повідомлення та гарантуємо, що підсумковий промпт не перевищує максимальний розмір
        last_text = message.text if message.text else '[медіа]'
        user_name = getattr(message.from_user, 'full_name', 'Невідомий') if message.from_user else 'Невідомий'
        suffix = f"\n{user_name}: {last_text}\n{PERSONA['name']}:"
        prompt = persona_prompt + "\n" + "\n".join(history) + suffix
        
        # Компресія промпту якщо занадто довгий
        while len(prompt) > PERSONA['max_context_size'] and history:
            history.pop(0)
            prompt = persona_prompt + "\n" + "\n".join(history) + suffix
        
        return await safe_api_call(_make_gemini_request, prompt)
        
    except Exception as e:
        logging.error(f"Помилка в process_message: {e}")
        return "Вибачте, сталася помилка при обробці повідомлення."

def _analyze_chat_mood(last_msgs: List[str]) -> str:
    """Аналізує настрій чату на основі останніх повідомлень."""
    if any('😂' in m or 'жарт' in m.lower() for m in last_msgs):
        return "В чаті зараз жартують."
    elif any('свар' in m.lower() or 'лайк' in m.lower() for m in last_msgs):
        return "В чаті сварка або напруга."
    elif all(len(m.strip()) < 2 for m in last_msgs):
        return "В чаті тиша."
    else:
        return "В чаті звичайна активність."

def _build_persona_prompt(mood_hint: str, tone_instruction: Optional[str] = None) -> str:
    """Будує базовий промпт для персони бота."""
    from bot.bot_config import PERSONA
    
    persona_prompt = (
        f"Ти — {PERSONA['name']}, дружелюбний україномовний чат-бот з легким гумором. "
        "Ти розумний, корисний та завжди готовий допомогти чи підтримати розмову. "
        "Твій стиль — це легкий гумор, дружелюбність та корисні поради. "
        "Ти адекватний, розумний та приємний у спілкуванні. "
        "Відповідай коротко, зрозуміло та по суті. "
        f"{mood_hint} Твоє завдання — бути корисним та приємним співрозмовником."
    )
    
    if tone_instruction:
        persona_prompt += f"\n\nСпеціальна інструкція: {tone_instruction}"
    
    return persona_prompt

async def _make_gemini_request(prompt: str) -> str:
    """Виконує запит до Gemini API."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не налаштовано")
        
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    params = {"key": GEMINI_API_KEY}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(GEMINI_API_URL, headers=headers, params=params, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError) as e:
                    logging.error(f"Помилка парсингу відповіді Gemini: {e}")
                    return "Вибачте, не вдалося отримати відповідь від AI."
            else:
                error_text = await resp.text()
                logging.error(f"Gemini API помилка {resp.status}: {error_text}")
                return "Помилка підключення до Gemini."

async def safe_api_call(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Безпечний виклик API з повторними спробами"""
    max_retries = 3
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(f"API виклик провалився після {max_retries} спроб: {e}")
                raise
            
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            logging.warning(f"API помилка (спроба {attempt + 1}/{max_retries}): {e}. Повтор через {delay}с")
            await asyncio.sleep(delay)
