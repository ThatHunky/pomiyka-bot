# Модуль для розумної автономності та анти-спам захисту
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict
from bot.bot_config import PERSONA

# Трекінг активності бота
bot_activity = defaultdict(list)  # chat_id -> [timestamps]
last_spontaneous = defaultdict(float)  # chat_id -> timestamp

def should_reply_smart(chat_id: int, message_text: str = "") -> bool:
    """Розумно визначає, чи варто відповісти"""
    now = time.time()
    
    # Очищуємо старі записи (старше години)
    hour_ago = now - 3600
    bot_activity[chat_id] = [ts for ts in bot_activity[chat_id] if ts > hour_ago]
    
    # Перевіряємо ліміт відповідей на годину
    if len(bot_activity[chat_id]) >= PERSONA["max_replies_per_hour"]:
        return False
    
    # Якщо згадано тригери - завжди відповідь (але з лімітом)
    message_lower = message_text.lower()
    if any(trigger.strip() in message_lower for trigger in PERSONA["trigger_keywords"]):
        return True
    
    # Інакше - випадкова відповідь з низькою ймовірністю
    return random.random() < PERSONA["smart_reply_chance"]

def should_be_spontaneous(chat_id: int) -> bool:
    """Визначає, чи час для спонтанної активності"""
    if not PERSONA["autonomous_mode"]:
        return False
    
    now = time.time()
    
    # Перевіряємо мінімальну паузу з останньої спонтанної активності
    min_silence = PERSONA["min_silence_minutes"] * 60
    if now - last_spontaneous[chat_id] < min_silence:
        return False
    
    # Перевіряємо ліміт на годину
    hour_ago = now - 3600
    bot_activity[chat_id] = [ts for ts in bot_activity[chat_id] if ts > hour_ago]
    if len(bot_activity[chat_id]) >= PERSONA["max_replies_per_hour"]:
        return False
    
    # Спонтанна активність з низькою ймовірністю
    return random.random() < PERSONA["spontaneous_chance"]

def mark_bot_activity(chat_id: int, is_spontaneous: bool = False):
    """Позначає активність бота"""
    now = time.time()
    bot_activity[chat_id].append(now)
    if is_spontaneous:
        last_spontaneous[chat_id] = now

def get_spontaneous_prompt(recent_messages: list) -> str:
    """Генерує prompt для спонтанної активності"""
    if not recent_messages:
        return (
            "Ти — Гряг, абсурдний дух чату. В чаті довго тиша. "
            "Напиши щось коротке, дивне, філософське або просто абсурдне, щоб нагадати про себе. "
            "Не питай нічого, просто будь загадковим."
        )
    
    context = " ".join(recent_messages[-3:])
    return (
        f"Ти — Гряг, абсурдний дух чату. Ось останні повідомлення: {context}. "
        "Напиши щось коротке, дотепне, що відноситься до контексту, але в абсурдному стилі. "
        "Не питай нічого, просто додай свій абсурдний коментар."
    )

def analyze_chat_mood(messages: list) -> str:
    """Аналізує настрій чату для кращого розуміння контексту"""
    if not messages:
        return "тиша"
    
    text_combined = " ".join([m.get("text", "") for m in messages[-5:]]).lower()
    
    # Аналіз емоцій
    if any(word in text_combined for word in ["😂", "хаха", "лол", "жарт", "прикол"]):
        return "веселий"
    elif any(word in text_combined for word in ["😢", "сумно", "біда", "проблема"]):
        return "сумний" 
    elif any(word in text_combined for word in ["😡", "злість", "сварка", "лайно"]):
        return "злий"
    elif any(word in text_combined for word in ["🤔", "думаю", "питання", "?"]):
        return "роздумливий"
    elif len(text_combined.strip()) < 10:
        return "тихий"
    else:
        return "нейтральний"
