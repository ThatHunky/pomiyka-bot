# Модуль для реакцій на повідомлення
import random
import asyncio
import logging
from aiogram.types import Message
from typing import List
from bot.bot_config import PERSONA

# Набір емоджі для реакцій (підтримується Telegram) - розширений
REACTION_EMOJIS = [
    "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", 
    "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩",
    "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳",
    "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡️", "🍌", "🏆",
    "😎", "🧐", "🤨", "👀", "🙌", "🚀", "🤝", "👊", 
    "🌟", "💪", "🎯", "🎮", "🎲", "🤘", "✌️", "🤞"
]

# Позитивні реакції для дружелюбних повідомлень (розширено)
POSITIVE_REACTIONS = [
    "👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🤩", "💯", "🏆",
    "😍", "🙌", "🚀", "🌟", "💪", "🤘", "✌️", "🤞"
]

# Нейтральні/цікаві реакції для звичайних повідомлень (розширено)
NEUTRAL_REACTIONS = [
    "🤔", "🤯", "🙏", "👌", "🕊", "🌚", "⚡️", "🍌",
    "😎", "🧐", "�", "👀", "�", "🎮", "�"
]

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
    reaction_chance = PERSONA.get("reaction_chance", 0.05)
    return random.random() < reaction_chance

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
            
            # Ставимо реакцію (треба передати як список)
            from aiogram.types import ReactionTypeEmoji
            await message.react([ReactionTypeEmoji(emoji=reaction)])
            return True
            
    except Exception as e:
        # Якщо реакція не вдалася (наприклад, бот не має прав), просто ігноруємо
        logging.debug(f"Не вдалося поставити реакцію: {e}")
        
    return False

def get_all_available_reactions() -> List[str]:
    """Повертає список всіх доступних реакцій"""
    return REACTION_EMOJIS.copy()
