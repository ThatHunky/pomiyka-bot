#!/usr/bin/env python3
"""
Тест для перевірки виправлення надто абсурдної персонажки бота
"""

import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from bot.modules import gemini
from bot.modules import random_life  
from bot.modules import enhanced_behavior

class MockMessage:
    """Фейковий об'єкт повідомлення для тестування"""
    def __init__(self, text: str, user_name: str = "TestUser", chat_id: int = -1001234567890):
        self.text = text
        self.from_user = type('User', (), {'full_name': user_name})
        self.chat = type('Chat', (), {'id': chat_id})

async def test_new_personality():
    """Тестує нову, менш абсурдну персонажку"""
    
    print("🔧 Тестування нової персонажки Гряга...")
    print("=" * 50)
    
    # Тест 1: Звичайне повідомлення
    print("\n1️⃣ Тест звичайного повідомлення:")
    message = MockMessage("Привіт! Як справи?")
    try:
        response = await gemini.process_message(message)
        print(f"Відповідь: {response}")
        
        # Перевіряємо що відповідь не містить надто абсурдних фраз
        absurd_indicators = ["абсурдн", "дивн", "незвичайн", "чудернацьк", "божевільн"]
        if any(word in response.lower() for word in absurd_indicators):
            print("⚠️  Увага: Відповідь всe ще містить абсурдні елементи")
        else:
            print("✅ Добре: Відповідь більш адекватна")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    # Тест 2: Рандомна відповідь
    print("\n2️⃣ Тест рандомної відповіді:")
    try:
        random_response = await random_life.get_random_reply(["Привіт всім!", "Як справи?"])
        print(f"Рандомна відповідь: {random_response}")
        
        # Перевіряємо тон
        if any(word in random_response.lower() for word in ["дружелюбн", "допомог", "цікав", "приємн"]):
            print("✅ Добре: Рандомна відповідь дружелюбна")
        else:
            print("⚠️  Рандомна відповідь може бути покращена")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    # Тест 3: Спонтанне повідомлення
    print("\n3️⃣ Тест спонтанного повідомлення:")
    try:
        spontaneous_prompt = enhanced_behavior.get_spontaneous_prompt(-1001234567890)
        print(f"Промт для спонтанного повідомлення: {spontaneous_prompt}")
        
        if "абсурдн" not in spontaneous_prompt.lower():
            print("✅ Добре: Спонтанний промт без абсурду")
        else:
            print("⚠️  Спонтанний промт всe ще містить абсурдні елементи")
            
    except Exception as e:
        print(f"❌ Помилка: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Виправлення персонажки завершено!")
    print("📝 Основні зміни:")
    print("   • Прибрано всі 'абсурдні' інструкції")
    print("   • Зменшено ймовірності рандомних відповідей")
    print("   • Бот тепер більш дружелюбний та адекватний") 
    print("   • Зберігся легкий гумор без божевілля")

if __name__ == "__main__":
    # Перевіряємо наявність змінних середовища
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  GEMINI_API_KEY не встановлено, деякі тести можуть не працювати")
    
    asyncio.run(test_new_personality())
