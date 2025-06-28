"""
Модуль для підрахунку токенів Gemini API
"""
import re
import logging
from typing import List, Dict, Any, Optional
from bot.bot_config import PERSONA

logger = logging.getLogger(__name__)

class TokenCounter:
    """Клас для оцінки кількості токенів в тексті"""
    
    def __init__(self):
        # Коефіцієнти для різних мов
        self.tokens_per_char: Dict[str, float] = {
            'ukrainian': float(PERSONA['tokens_per_char_ukrainian']),  # ~0.4 токена на символ
            'english': 0.25,  # ~0.25 токена на символ
            'mixed': 0.35  # змішаний текст
        }
        
    def estimate_tokens(self, text: str, language: str = 'ukrainian') -> int:
        """
        Оцінює кількість токенів в тексті
        
        Args:
            text: Текст для аналізу
            language: Мова тексту ('ukrainian', 'english', 'mixed')
            
        Returns:
            Оцінка кількості токенів
        """
        if not text:
            return 0
            
        # Очищаємо текст від зайвих пробілів
        cleaned_text = re.sub(r'\s+', ' ', text.strip())
        char_count = len(cleaned_text)
        
        # Коефіцієнт залежно від мови
        multiplier = self.tokens_per_char.get(language, self.tokens_per_char['mixed'])
        
        # Базова оцінка
        estimated_tokens = int(char_count * multiplier)
        
        # Додаткові коригування
        # Технічний текст (код, посилання) - більше токенів
        if self._is_technical_text(text):
            estimated_tokens = int(estimated_tokens * 1.2)
        
        # Емодзі та спецсимволи
        emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text))
        estimated_tokens += emoji_count
        
        return max(1, estimated_tokens)  # Мінімум 1 токен
    
    def _is_technical_text(self, text: str) -> bool:
        """Перевіряє чи містить текст технічні елементи"""
        technical_patterns = [
            r'https?://',  # URL
            r'[a-zA-Z_]\w*\([^)]*\)',  # Функції
            r'[{}\[\]]',  # Дужки коду
            r'[a-zA-Z_]\w*\.\w+',  # Атрибути об'єктів
            r'```.*?```',  # Блоки коду
            r'`[^`]+`',  # Інлайн код
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, text, re.DOTALL):
                return True
        return False
    
    def estimate_context_tokens(self, context: List[Dict[str, Any]]) -> int:
        """
        Оцінює загальну кількість токенів в контексті
        
        Args:
            context: Список повідомлень з полями 'text', 'user_name'
            
        Returns:
            Загальна оцінка токенів
        """
        total_tokens = 0
        
        for message in context:
            # Токени для імені користувача
            user_name = message.get('user_name', message.get('full_name', 'Невідомий'))
            total_tokens += self.estimate_tokens(user_name)
            
            # Токени для тексту повідомлення
            text = message.get('text', '')
            total_tokens += self.estimate_tokens(text)
            
            # Додаткові токени для форматування (ім'я: текст)
            total_tokens += 3  # ": " + розділювач
        
        return total_tokens
    
    def detect_language(self, text: str) -> str:
        """
        Визначає основну мову тексту
        
        Returns:
            'ukrainian', 'english', або 'mixed'
        """
        if not text:
            return 'mixed'
        
        # Підрахунок українських символів
        ukrainian_chars = len(re.findall(r'[абвгґдеєжзиіїйклмнопрстуфхцчшщьюя]', text.lower()))
        
        # Підрахунок англійських символів  
        english_chars = len(re.findall(r'[a-z]', text.lower()))
        
        total_letters = ukrainian_chars + english_chars
        
        if total_letters == 0:
            return 'mixed'
        
        ukrainian_ratio = ukrainian_chars / total_letters
        
        if ukrainian_ratio > 0.7:
            return 'ukrainian'
        elif ukrainian_ratio < 0.3:
            return 'english'
        else:
            return 'mixed'
    
    def compress_context_by_tokens(self, context: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """
        Стискає контекст до вказаної кількості токенів
        
        Args:
            context: Список повідомлень
            max_tokens: Максимальна кількість токенів
            
        Returns:
            Стиснений контекст
        """
        if not context:
            return []
        
        # Спочатку зберігаємо важливі повідомлення (згадки бота, команди)
        important_messages: List[Dict[str, Any]] = []
        regular_messages: List[Dict[str, Any]] = []
        
        for message in context:
            text = message.get('text', '').lower()
            is_important = (
                'гряг' in text or 
                '@gryag_bot' in text or
                text.startswith('/') or
                'бот' in text or
                len(text) > 100  # Довгі повідомлення можуть бути важливими
            )
            
            if is_important:
                important_messages.append(message)
            else:
                regular_messages.append(message)
        
        # Рахуємо токени для важливих повідомлень
        result: List[Dict[str, Any]] = []
        current_tokens = 0
        
        # Спочатку додаємо важливі повідомлення (останні)
        for message in reversed(important_messages[-10:]):  # Максимум 10 важливих
            tokens = self.estimate_context_tokens([message])
            if current_tokens + tokens <= max_tokens:
                result.insert(0, message)
                current_tokens += tokens
            else:
                break
        
        # Потім додаємо звичайні повідомлення (останні)
        for message in reversed(regular_messages):
            tokens = self.estimate_context_tokens([message])
            if current_tokens + tokens <= max_tokens:
                result.insert(0, message)
                current_tokens += tokens
            else:
                break
        
        # Сортуємо за хронологією (найстаріші спочатку)
        result.sort(key=lambda x: context.index(x) if x in context else 0)
        
        logger.info(f"Стиснено контекст: {len(context)} -> {len(result)} повідомлень, ~{current_tokens} токенів")
        
        return result

# Глобальний екземпляр
token_counter = TokenCounter()
