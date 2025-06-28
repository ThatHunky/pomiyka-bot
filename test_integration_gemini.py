#!/usr/bin/env python3
"""
Інтеграційний тест покращеного Gemini API модуля.
Перевіряє, що бот працює з новим Gemini enhanced модулем.
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

# Додаємо шлях до модулів бота
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

@pytest.mark.asyncio 
async def test_gemini_integration():
    """Тестує інтеграцію покращеного Gemini модуля з ботом."""
    
    # Імпортуємо модулі після додавання шляху
    from bot.modules import gemini
    from bot.modules.utils import FakeMessage
    
    # Створюємо тестове повідомлення
    test_message = FakeMessage(
        text="Привіт! Як справи?",
        chat_id=12345,
        user_name="Тест Користувач"
    )
    
    # Мокаємо HTTP запит до Gemini API
    mock_response = {
        "candidates": [{
            "content": {
                "parts": [{"text": "Привіт! У мене все добре, дякую! Як у тебе справи?"}],
                "role": "model"
            },
            "finishReason": "STOP"
        }],
        "usageMetadata": {
            "promptTokenCount": 10,
            "candidatesTokenCount": 15,
            "totalTokenCount": 25
        }
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        # Тестуємо базовий виклик
        response = await gemini.process_message(test_message)
        
        # Перевіряємо, що отримали відповідь
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        
        print(f"✅ Базова інтеграція працює. Відповідь: {response}")


@pytest.mark.asyncio
async def test_gemini_with_tone_instruction():
    """Тестує Gemini з інструкцією тону."""
    
    from bot.modules import gemini
    from bot.modules.utils import FakeMessage
    
    test_message = FakeMessage(
        text="Розкажи жарт",
        chat_id=12345,
        user_name="Тест Користувач"
    )
    
    tone_instruction = "Будь дуже веселим та використовуй багато емодзі"
    
    # Мокаємо HTTP запит
    mock_response = {
        "candidates": [{
            "content": {
                "parts": [{"text": "Ось веселий жарт! 😄 Чому програміст завжди плутає Різдво та Хелловін? 🎃🎄 Тому що OCT 31 == DEC 25! 😂"}],
                "role": "model"
            },
            "finishReason": "STOP"
        }],
        "usageMetadata": {
            "promptTokenCount": 20,
            "candidatesTokenCount": 30,
            "totalTokenCount": 50
        }
    }
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_post.return_value.__aenter__.return_value = mock_response_obj
        
        # Тестуємо з тоном
        response = await gemini.process_message(test_message, tone_instruction)
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        
        print(f"✅ Інтеграція з тоном працює. Відповідь: {response}")


@pytest.mark.asyncio
async def test_gemini_stats():
    """Тестує статистику Gemini API."""
    
    from bot.modules import gemini
    
    # Отримуємо статистику
    stats = await gemini.get_gemini_stats()
    
    # Перевіряємо структуру статистики
    assert isinstance(stats, dict)
    assert 'total_requests' in stats
    assert 'successful_requests' in stats
    assert 'total_tokens' in stats
    assert 'cache_hits' in stats
    
    print(f"✅ Статистика працює: {stats}")


@pytest.mark.asyncio
async def test_gemini_shutdown():
    """Тестує коректне завершення роботи Gemini модуля."""
    
    from bot.modules import gemini
    
    # Тестуємо shutdown (має пройти без помилок)
    await gemini.shutdown_gemini()
    
    print("✅ Shutdown працює коректно")


if __name__ == "__main__":
    pytest.main([__file__])
