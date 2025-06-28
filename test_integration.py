#!/usr/bin/env python3
"""
Простий тест інтеграції покращеної обробки контексту
"""

import sys
import os
import time

# Додаємо шлях до проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

def test_integration():
    """Тестує базову інтеграцію"""
    
    try:
        from bot.modules.utils import FakeMessage
        from bot.modules.enhanced_behavior import process_message_with_smart_context
        
        print("✅ Успішно імпортовано модулі")
        
        # Тест створення FakeMessage з новими параметрами
        fake_msg = FakeMessage(
            text="Тестове повідомлення",
            chat_id=123,
            user_name="Тестер",
            processed_context=[{"text": "контекст", "user": "Користувач", "timestamp": time.time()}],
            recommendations={"max_response_length": 100, "response_style": "concise"}
        )
        
        print(f"✅ FakeMessage створено: text='{fake_msg.text}', chat_id={fake_msg.chat.id}")
        print(f"   Контекст: {len(fake_msg.processed_context) if fake_msg.processed_context else 0} повідомлень")
        print(f"   Рекомендації: {fake_msg.recommendations}")
        
        # Тест базової обробки
        context = [
            {"text": "Привіт", "user": "Користувач1", "timestamp": time.time() - 100},
            {"text": "Як справи?", "user": "Користувач2", "timestamp": time.time() - 50},
        ]
        
        result = process_message_with_smart_context(
            "Простий тест",
            chat_id=123,
            context=context
        )
        
        print("✅ Процесор повідомлень працює")
        print(f"   Результат відповіді: {result['should_respond']}")
        print(f"   Тон: {result['response_tone']}")
        print(f"   Інструкція готова: {len(result['tone_instruction'])} символів")
        
        print("\n🎉 Базова інтеграція успішна!")
        return True
        
    except ImportError as e:
        print(f"❌ Помилка імпорту: {e}")
        return False
    except Exception as e:
        print(f"❌ Помилка тестування: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Тест базової інтеграції покращеної обробки контексту...")
    
    success = test_integration()
    
    if success:
        print("\n✅ Інтеграція готова!")
        print("\n📝 Основні покращення:")
        print("   • FakeMessage підтримує processed_context та recommendations")
        print("   • enhanced_behavior.process_message_with_smart_context() - головна функція")
        print("   • Gemini отримує рекомендації та обробленний контекст")
        print("   • Автоматичне стиснення великого контексту")
        print("   • Розумна обробка спаму")
        print("\n📌 Готово до використання в main.py")
    else:
        print("\n❌ Потрібні виправлення")
        exit(1)
