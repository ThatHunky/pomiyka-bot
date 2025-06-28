#!/usr/bin/env python3
"""
Тест для перевірки ігнорування старих повідомлень
"""
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import sys
import os

# Додаємо шлях до модулів бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from bot.main import is_message_too_old
from bot.bot_config import PERSONA

def test_old_messages():
    """Тестує функцію is_message_too_old"""
    print("=== Тестування ігнорування старих повідомлень ===")
    print(f"BOT_IGNORE_OLD_MESSAGES: {PERSONA['ignore_old_messages']}")
    print(f"BOT_MAX_MESSAGE_AGE_MINUTES: {PERSONA['max_message_age_minutes']}")
    print()
    
    # Створюємо фейкове повідомлення з різними датами
    now = datetime.now(timezone.utc)
    
    test_cases = [
        ("Свіже повідомлення (1 хв тому)", now - timedelta(minutes=1), False),
        ("Старе повідомлення (5 хв тому)", now - timedelta(minutes=5), False),  
        ("Дуже старе повідомлення (15 хв тому)", now - timedelta(minutes=15), True),
        ("Супер старе повідомлення (1 год тому)", now - timedelta(hours=1), True),
    ]
    
    for description, message_time, expected_ignored in test_cases:
        # Створюємо mock повідомлення
        mock_message = Mock()
        mock_message.date = message_time
        
        result = is_message_too_old(mock_message)
        status = "ІГНОРУЄТЬСЯ" if result else "ОБРОБЛЯЄТЬСЯ"
        expected = "ІГНОРУЄТЬСЯ" if expected_ignored else "ОБРОБЛЯЄТЬСЯ"
        
        print(f"{description}: {status} (очікувалось: {expected})")
        
        if result != expected_ignored:
            print(f"  ❌ ПОМИЛКА! Очікувалось {expected}, отримано {status}")
        else:
            print(f"  ✅ OK")
    
    print()
    print("=== Тест з вимкненим ігноруванням ===")
    
    # Тестуємо з вимкненим ігноруванням
    original_setting = PERSONA['ignore_old_messages']
    PERSONA['ignore_old_messages'] = False
    
    mock_message = Mock()
    mock_message.date = now - timedelta(hours=5)  # дуже старе
    
    result = is_message_too_old(mock_message)
    print(f"Дуже старе повідомлення (5 год) з вимкненим ігноруванням: {'ІГНОРУЄТЬСЯ' if result else 'ОБРОБЛЯЄТЬСЯ'}")
    
    if result:
        print("  ❌ ПОМИЛКА! Повідомлення не повинно ігноруватись коли функція вимкнена")
    else:
        print("  ✅ OK")
    
    # Відновлюємо налаштування
    PERSONA['ignore_old_messages'] = original_setting
    
    print()
    print("=== Тест завершено ===")

if __name__ == "__main__":
    test_old_messages()
