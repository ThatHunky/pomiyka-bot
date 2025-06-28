#!/usr/bin/env python3
"""
Тест покращень версії 3.0 для бота Гряг
Перевіряє нові функції персоналізації та контексту
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch

# Додаємо шлях до модулів бота
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

# Мокінг змінних середовища
os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
os.environ['GEMINI_API_KEY'] = 'test_key'
os.environ['BOT_ADMIN_ID'] = '123456789'

class TestContextImprovements:
    """Тести покращень контексту"""
    
    def test_context_with_usernames(self):
        """Тест формування контексту з іменами користувачів"""
        from bot.modules.context_enhanced import build_context
        
        # Мокінг функції get_recent_messages
        with patch('bot.modules.context_enhanced.get_recent_messages') as mock_get:
            mock_get.return_value = [
                {"full_name": "Олексій", "text": "Привіт всім!", "timestamp": "2025-06-28T10:00:00"},
                {"full_name": "Марія", "text": "Як справи?", "timestamp": "2025-06-28T10:01:00"},
                {"full_name": "Гряг", "text": "Вітаю! Все добре!", "timestamp": "2025-06-28T10:02:00"}
            ]
            
            result = build_context(12345, 10)
            
            # Перевіряємо, що контекст включає імена
            assert "Олексій: Привіт всім!" in result
            assert "Марія: Як справи?" in result
            assert "Гряг: Вітаю! Все добре!" in result
            
            print("✅ Тест контексту з іменами користувачів пройдено")

class TestRandomLifeImprovements:
    """Тести покращень random_life"""
    
    def test_expanded_replies(self):
        """Тест розширеного списку відповідей"""
        from bot.modules.random_life import RANDOM_REPLIES
        
        # Перевіряємо, що список розширено
        assert len(RANDOM_REPLIES) >= 30, f"Очікувалось >= 30 відповідей, отримано {len(RANDOM_REPLIES)}"
        
        # Перевіряємо різноманітність
        unique_words = set()
        for reply in RANDOM_REPLIES:
            unique_words.update(reply.lower().split())
        
        assert len(unique_words) > 50, "Недостатньо різноманітних слів у відповідях"
        
        print("✅ Тест розширеного списку відповідей пройдено")
    
    def test_cache_functionality(self):
        """Тест функціональності кешу"""
        from bot.modules.random_life import add_to_cache, is_similar_to_cached, last_messages_cache
        
        # Очищуємо кеш
        last_messages_cache.clear()
        
        # Додаємо повідомлення
        add_to_cache("Привіт, як справи?")
        add_to_cache("Що нового в житті?")
        
        # Перевіряємо схожість
        assert is_similar_to_cached("Привіт, як справи у вас?") == True
        assert is_similar_to_cached("Сьогодні чудова погода") == False
        
        print("✅ Тест функціональності кешу пройдено")

class TestEnhancedBehavior:
    """Тести покращеної поведінки"""
    
    def test_generate_enhanced_response(self):
        """Тест генерації покращених відповідей"""
        from bot.modules.enhanced_behavior import generate_enhanced_response
        
        # Створюємо мок повідомлення
        mock_message = Mock()
        mock_message.text = "Гряг, як справи з кодом?"
        mock_message.from_user = Mock()
        mock_message.from_user.full_name = "Тестовий користувач"
        
        mock_context = [
            {"user_name": "Тестовий користувач", "text": "Привіт!"},
            {"user_name": "Гряг", "text": "Вітаю!"}
        ]
        
        result = generate_enhanced_response(mock_message, mock_context)
        
        # Перевіряємо наявність ключових полів
        assert "should_reply" in result
        assert "tone_instruction" in result
        assert "conversation_type" in result
        assert "user_name" in result
        
        # Перевіряємо персоналізацію
        assert "Тестовий користувач" in result["tone_instruction"]
        
        print("✅ Тест генерації покращених відповідей пройдено")

class TestMainLogic:
    """Тести основної логіки"""
    
    def test_fake_message_class(self):
        """Тест класу FakeMessage"""
        from bot.main import FakeMessage
        
        fake_msg = FakeMessage(
            text="Тестове повідомлення",
            chat_id=12345,
            user_name="Тестер",
            processed_context="контекст",
            recommendations={"test": "value"}
        )
        
        assert fake_msg.text == "Тестове повідомлення"
        assert fake_msg.chat.id == 12345
        assert fake_msg.from_user.full_name == "Тестер"
        assert fake_msg.processed_context == "контекст"
        assert fake_msg.recommendations == {"test": "value"}
        
        print("✅ Тест класу FakeMessage пройдено")

def test_integration():
    """Інтеграційний тест покращень"""
    
    # Перевіряємо, що всі модулі можна імпортувати
    try:
        from bot.modules import context_enhanced, enhanced_behavior, random_life
        from bot.main import FakeMessage
        print("✅ Всі покращені модулі успішно імпортовано")
    except ImportError as e:
        pytest.fail(f"Помилка імпорту модулів: {e}")
    
    # Перевіряємо базову функціональність
    from bot.modules.random_life import RANDOM_REPLIES, should_reply_randomly
    
    assert len(RANDOM_REPLIES) > 20, "Список відповідей не розширено"
    assert should_reply_randomly("Привіт Гряг"), "Функція розпізнавання згадок не працює"
    
    print("✅ Інтеграційний тест пройдено")

if __name__ == "__main__":
    print("🧪 Запуск тестів покращень v3.0...")
    
    # Запускаємо тести
    pytest.main([__file__, "-v", "--tb=short"])
    
    print("🎉 Тестування завершено!")
