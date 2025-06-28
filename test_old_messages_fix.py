#!/usr/bin/env python3
"""
Тест ігнорування старих повідомлень - швидка перевірка нової логіки
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
from bot.bot_config import PERSONA

# Симуляція BOT_START_TIME
BOT_START_TIME = datetime.now(timezone.utc)

def is_message_too_old_test(message_date: datetime) -> bool:
    """Тестова версія функції перевірки старих повідомлень"""
    if not PERSONA["ignore_old_messages"]:
        return False
    if not message_date:
        return False
    
    # Конвертуємо message_time у UTC якщо потрібно
    message_time = message_date
    if message_time.tzinfo is None:
        message_time = message_time.replace(tzinfo=timezone.utc)
    
    # Повідомлення старе, якщо воно було створене ДО запуску бота
    # Додаємо невелику буферну зону (30 секунд) для часових розбіжностей
    buffer_zone = timedelta(seconds=30)
    cutoff_time = BOT_START_TIME - buffer_zone
    
    if message_time < cutoff_time:
        print(f"🕰️ Старе повідомлення: створено {message_time}, бот запущено {BOT_START_TIME}")
        return True
    
    return False

def test_old_message_logic():
    """Тестуємо логіку ігнорування старих повідомлень"""
    print("🧪 Тестування логіки ігнорування старих повідомлень")
    print(f"⏰ Симуляція запуску бота: {BOT_START_TIME}")
    print(f"🛡️ Ігнорування включено: {PERSONA['ignore_old_messages']}")
    print("-" * 60)
    
    # Тест 1: Дуже старе повідомлення (1 годину назад)
    old_message = BOT_START_TIME - timedelta(hours=1)
    result1 = is_message_too_old_test(old_message)
    print(f"1️⃣ Повідомлення 1 год назад: {old_message} → {'ІГНОРУЄМО' if result1 else 'ОБРОБЛЯЄМО'}")
    
    # Тест 2: Повідомлення 5 хвилин назад
    medium_old = BOT_START_TIME - timedelta(minutes=5)
    result2 = is_message_too_old_test(medium_old)
    print(f"2️⃣ Повідомлення 5 хв назад: {medium_old} → {'ІГНОРУЄМО' if result2 else 'ОБРОБЛЯЄМО'}")
    
    # Тест 3: Повідомлення 1 хвилину назад (але до запуску)
    slightly_old = BOT_START_TIME - timedelta(minutes=1)
    result3 = is_message_too_old_test(slightly_old)
    print(f"3️⃣ Повідомлення 1 хв назад: {slightly_old} → {'ІГНОРУЄМО' if result3 else 'ОБРОБЛЯЄМО'}")
    
    # Тест 4: Нове повідомлення (після запуску)
    new_message = BOT_START_TIME + timedelta(seconds=10)
    result4 = is_message_too_old_test(new_message)
    print(f"4️⃣ Нове повідомлення: {new_message} → {'ІГНОРУЄМО' if result4 else 'ОБРОБЛЯЄМО'}")
    
    # Тест 5: Повідомлення в буферній зоні (25 секунд назад)
    buffer_message = BOT_START_TIME - timedelta(seconds=25)
    result5 = is_message_too_old_test(buffer_message)
    print(f"5️⃣ Буферна зона (25с назад): {buffer_message} → {'ІГНОРУЄМО' if result5 else 'ОБРОБЛЯЄМО'}")
    
    print("-" * 60)
    
    # Очікувані результати
    expected = [True, True, True, False, False]  # перші 3 старі, останні 2 нові
    actual = [result1, result2, result3, result4, result5]
    
    if expected == actual:
        print("✅ Всі тести пройдено! Логіка працює правильно.")
        return True
    else:
        print("❌ Тести не пройдено!")
        print(f"Очікувано: {expected}")
        print(f"Отримано:  {actual}")
        return False

if __name__ == "__main__":
    success = test_old_message_logic()
    exit(0 if success else 1)
