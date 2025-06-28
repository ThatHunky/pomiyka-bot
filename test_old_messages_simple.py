#!/usr/bin/env python3
"""
Тест для перевірки ігнорування старих повідомлень
"""
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import os
from dotenv import load_dotenv

# Завантажуємо змінні середовища
load_dotenv()

def is_message_too_old_test(message, ignore_old_messages=True, max_message_age_minutes=10):
    """Тестова версія функції is_message_too_old"""
    if not ignore_old_messages:
        return False
    if not message.date:
        return False
    
    now = datetime.now(timezone.utc)
    message_time = message.date
    
    # Конвертуємо message_time у UTC якщо потрібно
    if message_time.tzinfo is None:
        message_time = message_time.replace(tzinfo=timezone.utc)
    
    age_minutes = (now - message_time).total_seconds() / 60
    
    if age_minutes > max_message_age_minutes:
        print(f"Ігноруємо старе повідомлення (вік: {age_minutes:.1f} хв, максимум: {max_message_age_minutes} хв)")
        return True
    
    return False

def test_old_messages():
    """Тестує функцію is_message_too_old"""
    print("=== Тестування ігнорування старих повідомлень ===")
    
    # Отримуємо налаштування з .env
    ignore_old = os.getenv("BOT_IGNORE_OLD_MESSAGES", "true").lower() == "true"
    max_age = int(os.getenv("BOT_MAX_MESSAGE_AGE_MINUTES", "10"))
    
    print(f"BOT_IGNORE_OLD_MESSAGES: {ignore_old}")
    print(f"BOT_MAX_MESSAGE_AGE_MINUTES: {max_age}")
    print()
    
    # Створюємо фейкове повідомлення з різними датами
    now = datetime.now(timezone.utc)
    
    test_cases = [
        ("Свіже повідомлення (1 хв тому)", now - timedelta(minutes=1), False),
        ("Нормальне повідомлення (5 хв тому)", now - timedelta(minutes=5), False),  
        ("Старе повідомлення (15 хв тому)", now - timedelta(minutes=15), True),
        ("Дуже старе повідомлення (1 год тому)", now - timedelta(hours=1), True),
    ]
    
    for description, message_time, expected_ignored in test_cases:
        # Створюємо mock повідомлення
        mock_message = Mock()
        mock_message.date = message_time
        
        result = is_message_too_old_test(mock_message, ignore_old, max_age)
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
    mock_message = Mock()
    mock_message.date = now - timedelta(hours=5)  # дуже старе
    
    result = is_message_too_old_test(mock_message, False, max_age)
    print(f"Дуже старе повідомлення (5 год) з вимкненим ігноруванням: {'ІГНОРУЄТЬСЯ' if result else 'ОБРОБЛЯЄТЬСЯ'}")
    
    if result:
        print("  ❌ ПОМИЛКА! Повідомлення не повинно ігноруватись коли функція вимкнена")
    else:
        print("  ✅ OK")
    
    print()
    print("=== Тест завершено ===")

if __name__ == "__main__":
    test_old_messages()
