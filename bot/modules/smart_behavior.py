# Модуль для розумної автономності та анти-спам захисту
import time
import random
from datetime import datetime, timedelta
from collections import defaultdict
from bot.bot_config import PERSONA

# Трекінг активності бота та користувачів
bot_activity = defaultdict(list)  # chat_id -> [timestamps]
user_activity = defaultdict(lambda: defaultdict(list))  # chat_id -> user_id -> [timestamps]
last_spontaneous = defaultdict(float)  # chat_id -> timestamp
spam_timeouts = defaultdict(float)  # chat_id -> end_timeout_timestamp

def track_user_activity(chat_id: int, user_id: int):
    """Відстежує активність користувача для анти-спам системи"""
    now = time.time()
    user_activity[chat_id][user_id].append(now)
    
    # Очищуємо старі записи (старше хвилини)
    minute_ago = now - 60
    user_activity[chat_id][user_id] = [ts for ts in user_activity[chat_id][user_id] if ts > minute_ago]

def is_spam_detected(chat_id: int, user_id: int = None) -> bool:
    """Перевіряє чи виявлено спам у чаті"""
    now = time.time()
    
    # Перевіряємо чи чат все ще в таймауті
    if now < spam_timeouts[chat_id]:
        return True
    
    if user_id:
        # Перевіряємо активність конкретного користувача
        recent_messages = len(user_activity[chat_id][user_id])
        if recent_messages >= PERSONA["spam_threshold"]:
            # Встановлюємо таймаут для чату
            spam_timeouts[chat_id] = now + PERSONA["spam_timeout"]
            return True
    
    return False

def get_spam_reply() -> str:
    """Повертає випадкову відповідь на спам"""
    return random.choice(PERSONA["spam_replies"])

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
    min_silence = PERSONA["spontaneous_min_pause"] * 60
    if now - last_spontaneous[chat_id] < min_silence:
        return False
    
    # Перевіряємо ліміт на годину
    hour_ago = now - 3600
    bot_activity[chat_id] = [ts for ts in bot_activity[chat_id] if ts > hour_ago]
    if len(bot_activity[chat_id]) >= PERSONA["max_replies_per_hour"]:
        return False
    
    # Спонтанна активність з низькою ймовірністю, але вища після довгої тиші
    base_chance = PERSONA["spontaneous_chance"]
    
    # Збільшуємо шанс, якщо довго не було спонтанних повідомлень
    time_since_last = now - last_spontaneous[chat_id]
    if time_since_last > 7200:  # 2 години
        base_chance *= 3
    elif time_since_last > 3600:  # 1 година
        base_chance *= 2
    
    return random.random() < base_chance

def mark_bot_activity(chat_id: int, is_spontaneous: bool = False):
    """Позначає активність бота"""
    now = time.time()
    bot_activity[chat_id].append(now)
    if is_spontaneous:
        last_spontaneous[chat_id] = now

def get_spontaneous_prompt(recent_messages: list) -> str:
    """Генерує prompt для спонтанної активності"""
    mood = analyze_chat_mood(recent_messages) if recent_messages else "тиша"
    
    if not recent_messages:
        prompts = [
            "Ти — Гряг, абсурдний дух чату. В чаті довго тиша. Напиши щось коротке, загадкове або філософське.",
            "Ти — Гряг. Чат замовк. Нагадай про себе якимось абсурдним коментарем або думкою.",
            "Ти — Гряг. Тиша в чаті. Скажи щось дивне, але дотепне, щоб розбавити атмосферу.",
            "Ти — Гряг. Довга тиша. Поділися якоюсь абсурдною мудрістю або спостереженням."
        ]
        return random.choice(prompts)
    
    context = " ".join(recent_messages[-3:])
    
    mood_prompts = {
        "веселий": f"Ти — Гряг. В чаті весело: {context}. Додай свій абсурдний коментар до веселощів.",
        "сумний": f"Ти — Гряг. В чаті сумно: {context}. Скажи щось абсурдно-підбадьорливе.",
        "злий": f"Ти — Гряг. В чаті напруга: {context}. Розрядь ситуацію абсурдним коментарем.",
        "роздумливий": f"Ти — Гряг. В чаті роздуми: {context}. Додай свою абсурдну філософію.",
        "тихий": f"Ти — Гряг. Чат притих: {context}. Скажи щось дивне, щоб оживити атмосферу.",
    }
    
    default_prompt = f"Ти — Гряг. Останні повідомлення: {context}. Скажи щось абсурдне, що стосується контексту."
    return mood_prompts.get(mood, default_prompt)

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
