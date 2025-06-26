# Модуль для реакцій на повідомлення
import random
import asyncio
from aiogram.types import Message
from bot.bot_config import PERSONA

# Набір емоджі для реакцій (підтримується Telegram)
REACTION_EMOJIS = [
    "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", 
    "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩",
    "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳",
    "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡️", "🍌", "🏆"
]

# Позитивні реакції для дружелюбних повідомлень
POSITIVE_REACTIONS = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "💯", "🏆"]

# Нейтральні/абсурдні реакції для звичайних повідомлень  
NEUTRAL_REACTIONS = ["🤔", "🤯", "🙏", "👌", "🕊", "🤡", "🌚", "🌭", "⚡️", "🍌"]

# Негативні реакції (рідко використовуються)
NEGATIVE_REACTIONS = ["👎", "🤬", "😢", "🤮", "💩", "🥱", "🥴"]

def should_react_to_message(message: Message) -> bool:
    """Визначає, чи потрібно ставити реакцію на повідомлення"""
    if not message.text:
        return False
    
    text = message.text.lower()
    
    # Завжди реагуємо на згадки бота
    bot_triggers = ["гряг", "@gryag_bot", "грягік", "бот"]
    if any(trigger in text for trigger in bot_triggers):
        return random.random() < 0.7  # 70% шанс реакції на згадку
    
    # Реагуємо на питання
    if "?" in text or any(word in text for word in ["що", "як", "коли", "де", "чому", "хто"]):
        return random.random() < 0.3  # 30% шанс на питання
    
    # Реагуємо на емоційні повідомлення
    emotional_words = ["класно", "супер", "крута", "лайно", "дурня", "блін", "ого", "вау"]
    if any(word in text for word in emotional_words):
        return random.random() < 0.4  # 40% шанс на емоційні слова
    
    # Рандомна реакція на звичайні повідомлення (рідко)
    return random.random() < PERSONA.get("reaction_chance", 0.05)  # 5% базовий шанс

def get_reaction_for_message(message: Message) -> str:
    """Вибирає підходящу реакцію для повідомлення"""
    if not message.text:
        return random.choice(NEUTRAL_REACTIONS)
    
    text = message.text.lower()
    
    # Позитивні слова = позитивні реакції
    positive_words = ["класно", "супер", "крута", "дякую", "круто", "молодець", "вау", "ого"]
    if any(word in text for word in positive_words):
        return random.choice(POSITIVE_REACTIONS)
    
    # Негативні слова = нейтральні/абсурдні реакції (не хочемо підтримувати негатив)
    negative_words = ["лайно", "дурня", "блін", "поганий", "жах"]
    if any(word in text for word in negative_words):
        return random.choice(NEUTRAL_REACTIONS)
    
    # Згадки бота = позитивні реакції
    bot_triggers = ["гряг", "@gryag_bot", "грягік", "бот"]
    if any(trigger in text for trigger in bot_triggers):
        return random.choice(POSITIVE_REACTIONS)
    
    # Питання = задумливі реакції
    if "?" in text:
        return random.choice(["🤔", "🤯", "👌", "🙏"])
    
    # За замовчуванням - нейтральні/абсурдні
    return random.choice(NEUTRAL_REACTIONS)

async def maybe_react_to_message(message: Message) -> bool:
    """Можливо ставить реакцію на повідомлення. Повертає True якщо реакцію поставлено."""
    try:
        if should_react_to_message(message):
            reaction = get_reaction_for_message(message)
            
            # Невелика затримка щоб виглядало природно
            await asyncio.sleep(random.uniform(0.5, 2.0))
            
            # Ставимо реакцію
            await message.react(reaction)
            return True
            
    except Exception as e:
        # Якщо реакція не вдалася (наприклад, бот не має прав), просто ігноруємо
        import logging
        logging.debug(f"Не вдалося поставити реакцію: {e}")
        
    return False

def get_all_available_reactions() -> list:
    """Повертає список всіх доступних реакцій"""
    return REACTION_EMOJIS.copy()
