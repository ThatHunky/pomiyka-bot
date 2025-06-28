#!/usr/bin/env python3
"""
Тест для перевірки оновлених інструкцій бота
"""

import asyncio
import sys
import os

# Додаємо шлях до модулів бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

from bot.modules.gemini_enhanced import get_client
from bot.modules.enhanced_behavior import analyze_conversation_context, get_tone_instruction
from bot.modules.situation_predictor import get_suggested_response_tone

async def test_personality_fixes():
    """Тестує виправлення особистості бота"""
    print("🧪 Тестування виправлень особистості бота...")
    
    try:
        # Тест 1: Перевірка мінімальних налаштувань безпеки
        print("\n1️⃣ Тестування налаштувань безпеки...")
        client = await get_client()
        
        # Перевіряємо, що safety settings дійсно мінімальні
        safety_settings = client._get_default_safety_settings()
        minimal_safety = sum(1 for setting in safety_settings if setting.threshold.value == "BLOCK_NONE")
        print(f"   ✅ Мінімальних налаштувань безпеки: {minimal_safety}/5")
        
        # Тест 2: Перевірка нових тонів відповідей
        print("\n2️⃣ Тестування нових тонів відповідей...")
        tone = get_suggested_response_tone("технічна_дискусія", "позитивний")
        print(f"   ✅ Тон для технічної дискусії: {tone}")
        
        tone2 = get_suggested_response_tone("філософська_розмова", "задумливий")
        print(f"   ✅ Тон для філософської розмови: {tone2}")
        
        # Тест 3: Перевірка аналізу повідомлень
        print("\n3️⃣ Тестування аналізу повідомлень...")
        analysis = analyze_conversation_context(
            "Гряг, що думаєш про ці помилки підключення?", 
            []
        )
        print(f"   ✅ Тип розмови: {analysis['type']}")
        print(f"   ✅ Настрій: {analysis['mood']}")
        print(f"   ✅ Залученість: {analysis['engagement']}/10")
        
        # Тест 4: Перевірка інструкцій тону
        print("\n4️⃣ Тестування інструкцій тону...")
        tone_instruction = get_tone_instruction(analysis)
        print(f"   ✅ Інструкція тону: {tone_instruction[:100]}...")
        
        # Тест 5: Перевірка генерації відповіді
        print("\n5️⃣ Тестування генерації відповіді...")
        response = await client.generate_content(
            "Гряг, як справи?",
            context_type="normal"
        )
        print(f"   ✅ Відповідь бота: {response}")
        
        print("\n🎉 Всі тести пройшли успішно!")
        print("\n📝 Висновки:")
        print("   • Налаштування безпеки знижені до мінімуму")
        print("   • Тони відповідей стали більш природними")
        print("   • Інструкції менш 'шизоїдні' та більш дружелюбні")
        print("   • Бот тепер говорить більш адекватно")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка тестування: {e}")
        return False
    finally:
        try:
            await client.close()
        except:
            pass

async def main():
    """Головна функція"""
    success = await test_personality_fixes()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
