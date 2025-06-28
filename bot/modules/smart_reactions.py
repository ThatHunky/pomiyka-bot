"""
Модуль розумних реакцій бота.
Автоматично додає емодзі-реакції на повідомлення залежно від контексту.
"""

import random
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiogram.types import Message, ReactionTypeEmoji
from aiogram import Bot

logger = logging.getLogger(__name__)


@dataclass
class ReactionConfig:
    """Конфігурація реакцій"""
    mention_chance: float = 0.7  # 70% шанс реакції на згадки
    question_chance: float = 0.3  # 30% шанс на питання
    regular_chance: float = 0.05  # 5% шанс на звичайні повідомлення
    max_reactions_per_minute: int = 5
    min_pause_between_reactions: int = 3  # секунди


class SmartReactions:
    """Система розумних реакцій"""
    
    def __init__(self, bot: Bot, config: Optional[ReactionConfig] = None):
        self.bot = bot
        self.config = config or ReactionConfig()
        self.last_reactions: Dict[int, datetime] = {}
        self.reaction_count: Dict[int, List[datetime]] = {}
        
        # Основні емодзі для реакцій
        self.positive_emojis = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🙏", "👌", "⚡️"]
        self.neutral_emojis = ["🤔", "🤯", "🌚", "🤡", "🌭", "🍌"]
        self.thoughtful_emojis = ["🤔", "💭", "🧐", "💡", "🎯"]
        self.absurd_emojis = ["🤡", "🌚", "🌭", "🍌", "🦄", "🚀"]
        
        # Тригери для згадок бота
        self.triggers = [
            "гряг", "грягік", "грягу", "гряга", "грягом",
            "бот", "боте", "@gryag_bot", "gryag"
        ]
        
        # Позитивні слова
        self.positive_words = [
            "дякую", "спасибі", "круто", "класно", "супер", "чудово",
            "відмінно", "молодець", "красиво", "прекрасно", "любов"
        ]
        
        # Слова-питання
        self.question_words = ["що", "де", "коли", "як", "чому", "хто", "чи", "скільки"]

    async def should_react(self, message: Message) -> Tuple[bool, str]:
        """Визначає, чи потрібно реагувати на повідомлення"""
        try:
            chat_id = message.chat.id
            current_time = datetime.now()
            
            # Перевірка ліміту реакцій
            if not self._check_rate_limit(chat_id, current_time):
                return False, "rate_limit"
            
            # Перевірка мінімальної паузи
            if chat_id in self.last_reactions:
                time_diff = (current_time - self.last_reactions[chat_id]).total_seconds()
                if time_diff < self.config.min_pause_between_reactions:
                    return False, "min_pause"
            
            text = message.text or message.caption or ""
            text_lower = text.lower()
            
            # Згадки бота - 70% шанс
            if any(trigger in text_lower for trigger in self.triggers):
                if random.random() < self.config.mention_chance:
                    return True, "mention"
            
            # Питання - 30% шанс
            if self._is_question(text):
                if random.random() < self.config.question_chance:
                    return True, "question"
            
            # Звичайні повідомлення - 5% шанс
            if random.random() < self.config.regular_chance:
                return True, "regular"
            
            return False, "no_trigger"
            
        except Exception as e:
            logger.error(f"Помилка при визначенні реакції: {e}")
            return False, "error"

    def _check_rate_limit(self, chat_id: int, current_time: datetime) -> bool:
        """Перевірка ліміту реакцій за хвилину"""
        if chat_id not in self.reaction_count:
            self.reaction_count[chat_id] = []
        
        # Очищення старих записів
        minute_ago = current_time - timedelta(minutes=1)
        self.reaction_count[chat_id] = [
            time for time in self.reaction_count[chat_id] 
            if time > minute_ago
        ]
        
        # Перевірка ліміту
        return len(self.reaction_count[chat_id]) < self.config.max_reactions_per_minute

    def _is_question(self, text: str) -> bool:
        """Визначає, чи є повідомлення питанням"""
        if not text:
            return False
        
        text_lower = text.lower().strip()
        
        # Пряма перевірка знаку питання
        if text.endswith("?"):
            return True
        
        # Перевірка слів-питань
        words = text_lower.split()
        if words and words[0] in self.question_words:
            return True
        
        return False

    async def get_reaction_emoji(self, message: Message, reaction_type: str) -> str:
        """Вибирає підходящий емодзі для реакції"""
        try:
            text = message.text or message.caption or ""
            text_lower = text.lower()
            
            # Позитивні слова - позитивні емодзі
            if any(word in text_lower for word in self.positive_words):
                return random.choice(self.positive_emojis)
            
            # Питання - задумливі емодзі
            if reaction_type == "question":
                return random.choice(self.thoughtful_emojis)
            
            # Згадки бота - різноманітні емодзі
            if reaction_type == "mention":
                all_emojis = self.positive_emojis + self.neutral_emojis
                return random.choice(all_emojis)
            
            # Звичайні повідомлення - нейтральні/абсурдні
            return random.choice(self.neutral_emojis + self.absurd_emojis)
            
        except Exception as e:
            logger.error(f"Помилка при виборі емодзі: {e}")
            return random.choice(self.positive_emojis)

    async def add_reaction(self, message: Message) -> bool:
        """Додає реакцію на повідомлення"""
        try:
            should_react, reaction_type = await self.should_react(message)
            
            if not should_react:
                logger.debug(f"Не реагуємо: {reaction_type}")
                return False
            
            emoji = await self.get_reaction_emoji(message, reaction_type)
            
            # Додавання реакції через простий API
            try:
                await self.bot.set_message_reaction(
                    chat_id=message.chat.id,
                    message_id=message.message_id,
                    reaction=[ReactionTypeEmoji(emoji=emoji)]
                )
            except Exception as e:
                logger.warning(f"Не вдалося додати реакцію {emoji}: {e}")
                return False
            
            # Оновлення статистики
            chat_id = message.chat.id
            current_time = datetime.now()
            self.last_reactions[chat_id] = current_time
            
            if chat_id not in self.reaction_count:
                self.reaction_count[chat_id] = []
            self.reaction_count[chat_id].append(current_time)
            
            logger.info(f"Додано реакцію {emoji} на повідомлення в чаті {chat_id} (тип: {reaction_type})")
            return True
            
        except Exception as e:
            logger.error(f"Помилка при додаванні реакції: {e}")
            return False

    async def process_message(self, message: Message) -> Optional[Dict[str, Any]]:
        """Обробляє повідомлення для можливої реакції"""
        try:
            # Ігноруємо повідомлення бота
            if message.from_user and message.from_user.is_bot:
                return None
            
            # Додаємо реакцію
            reaction_added = await self.add_reaction(message)
            
            return {
                "reaction_added": reaction_added,
                "chat_id": message.chat.id,
                "message_id": message.message_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Помилка при обробці повідомлення для реакції: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Повертає статистику реакцій"""
        try:
            current_time = datetime.now()
            total_reactions = 0
            active_chats = 0
            
            for reactions in self.reaction_count.values():
                # Підрахунок реакцій за останню годину
                hour_ago = current_time - timedelta(hours=1)
                recent_reactions = [r for r in reactions if r > hour_ago]
                
                if recent_reactions:
                    active_chats += 1
                    total_reactions += len(recent_reactions)
            
            return {
                "total_reactions_last_hour": total_reactions,
                "active_chats": active_chats,
                "total_tracked_chats": len(self.reaction_count),
                "config": {
                    "mention_chance": self.config.mention_chance,
                    "question_chance": self.config.question_chance,
                    "regular_chance": self.config.regular_chance,
                    "max_reactions_per_minute": self.config.max_reactions_per_minute
                }
            }
            
        except Exception as e:
            logger.error(f"Помилка при отриманні статистики реакцій: {e}")
            return {"error": str(e)}

    async def cleanup_old_data(self):
        """Очищення старих даних"""
        try:
            current_time = datetime.now()
            hour_ago = current_time - timedelta(hours=1)
            
            # Очищення старих реакцій
            for chat_id in list(self.reaction_count.keys()):
                self.reaction_count[chat_id] = [
                    time for time in self.reaction_count[chat_id] 
                    if time > hour_ago
                ]
                
                # Видалення порожніх списків
                if not self.reaction_count[chat_id]:
                    del self.reaction_count[chat_id]
            
            # Очищення старих записів last_reactions
            for chat_id in list(self.last_reactions.keys()):
                if current_time - self.last_reactions[chat_id] > timedelta(hours=24):
                    del self.last_reactions[chat_id]
            
            logger.debug("Очищення старих даних реакцій завершено")
            
        except Exception as e:
            logger.error(f"Помилка при очищенні старих даних реакцій: {e}")


# Фабрика для створення екземпляру
def create_smart_reactions(bot: Bot, config: Optional[Dict[str, Any]] = None) -> SmartReactions:
    """Створює екземпляр SmartReactions з конфігурацією"""
    reaction_config = ReactionConfig()
    
    if config:
        reaction_config.mention_chance = config.get("mention_chance", 0.7)
        reaction_config.question_chance = config.get("question_chance", 0.3)
        reaction_config.regular_chance = config.get("regular_chance", 0.05)
        reaction_config.max_reactions_per_minute = config.get("max_reactions_per_minute", 5)
        reaction_config.min_pause_between_reactions = config.get("min_pause_between_reactions", 3)
    
    return SmartReactions(bot, reaction_config)
