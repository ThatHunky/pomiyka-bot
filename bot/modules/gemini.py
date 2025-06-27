# Модуль для інтеграції з Gemini (конфігуруємо модель)
import aiohttp
from aiogram.types import Message
from . import context
import os
from dotenv import load_dotenv
load_dotenv()

from bot.bot_config import GEMINI_MODEL

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def process_message(message: Message, tone_instruction: str | None = None) -> str:
    from bot.bot_config import PERSONA
    chat_context = context.get_context(message.chat.id)
    
    # Додаємо абсурдну інструкцію та динамічний опис обстановки
    last_msgs = [m['text'] for m in chat_context[-5:]]
    mood_hint = ""
    if any('😂' in m or 'жарт' in m.lower() for m in last_msgs):
        mood_hint = "В чаті зараз жартують."
    elif any('свар' in m.lower() or 'лайк' in m.lower() for m in last_msgs):
        mood_hint = "В чаті сварка або напруга."
    elif all(len(m.strip()) < 2 for m in last_msgs):
        mood_hint = "В чаті тиша."
    else:
        mood_hint = "В чаті звичайна активність."
    
    # Базова персона
    persona_prompt = (
        f"Ти — {PERSONA['name']}, дружелюбний україномовний чат-бот з легким гумором. "
        "Ти розумний, корисний та завжди готовий допомогти чи підтримати розмову. "
        "Твій стиль — це легкий гумор, дружелюбність та корисні поради. "
        "Ти адекватний, розумний та приємний у спілкуванні. "
        "Відповідай коротко, зрозуміло та по суті. "
        f"{mood_hint} Твоє завдання — бути корисним та приємним співрозмовником."
    )
    
    # Додаємо спеціальну інструкцію тону, якщо є
    if tone_instruction:
        persona_prompt += f"\n\nСпеціальна інструкція: {tone_instruction}"
    
    # Формуємо повний промт з контекстом
    prompt = persona_prompt + "\n" + "\n".join([f"{m['user']}: {m['text']}" for m in chat_context[-PERSONA['context_limit']:]])
    
    # Додаємо поточне повідомлення
    last_text = message.text if message.text else '[медіа]'
    prompt += f"\n{message.from_user.full_name}: {last_text}\n{PERSONA['name']}:"
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
                except Exception:
                    return "Вибачте, не вдалося отримати відповідь від AI."
            else:
                return "Помилка підключення до Gemini."
