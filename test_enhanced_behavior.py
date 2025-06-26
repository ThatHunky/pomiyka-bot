#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

def test_enhanced_behavior():
    """Тестування нового модуля аналізу контексту"""
    print("🧪 Тестування системи передбачення ситуацій...")
    
    try:
        # Імпорт модуля
        from bot.modules.enhanced_behavior import (
            analyze_conversation_context, 
            create_context_aware_prompt,
            get_chat_trends,
            should_intervene_spontaneously
        )
        print("✅ Модуль успішно імпортовано")
        
        # Тестові повідомлення з різних ситуацій
        test_messages = [
            "Привіт Гряг, як справи?",
            "Хаха, це дуже смішно! 😂",
            "У мене проблема з кодом в Python",
            "Що таке життя і в чому сенс буття?",
            "Дурень, ти нічого не розумієш!",
            "Сьогодні погода чудова"
        ]
        
        print("\n📊 Результати аналізу:")
        print("-" * 50)
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. Повідомлення: '{message}'")
            
            # Аналізуємо контекст
            analysis = analyze_conversation_context(message)
            
            print(f"   Тип: {analysis['type']}")
            print(f"   Настрій: {analysis['mood']}")
            print(f"   Залученість: {analysis['engagement']}/10")
            print(f"   Варто відповісти: {analysis['should_respond']}")
            print(f"   Тон: {analysis['response_tone']}")
            
            # Якщо варто відповісти, показуємо промт
            if analysis['should_respond']:
                prompt = create_context_aware_prompt(message, analysis)
                print(f"   💬 Промт (перші 100 символів): {prompt[:100]}...")
        
        print("\n🎯 Тест спеціального повідомлення зі скріну:")
        special_message = "Гряг? О, це не помилка підключення, це колекція помилок підключення, як таємничі перлини на дні океану інтернету."
        analysis = analyze_conversation_context(special_message)
        
        print(f"Повідомлення: '{special_message}'")
        print(f"Тип: {analysis['type']}")
        print(f"Настрій: {analysis['mood']}")
        print(f"Залученість: {analysis['engagement']}/10")
        print(f"Варто відповісти: {analysis['should_respond']}")
        print(f"Тон: {analysis['response_tone']}")
        
        if analysis['should_respond']:
            prompt = create_context_aware_prompt(special_message, analysis)
            print(f"\n💭 Згенерований промт:")
            print("=" * 60)
            print(prompt)
            print("=" * 60)
        
        print("\n✅ Всі тести пройшли успішно!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_enhanced_behavior()
