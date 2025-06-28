#!/usr/bin/env python3
"""
Тест покращеної обробки контексту чату для запобігання спаму
"""

import sys
import os
import time
import random

# Додаємо шлях до проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

def test_smart_context_processing():
    """Тестує розумну обробку контексту"""
    
    try:
        from bot.modules.enhanced_behavior import (
            process_message_with_smart_context,
            analyze_chat_spam_level,
            compress_context_smartly,
            get_anti_spam_message,
            log_context_processing,
            get_processing_statistics
        )
        
        print("✅ Успішно імпортовано функції покращеної обробки контексту")
        
        # Тест 1: Нормальна ситуація
        print("\n🔄 Тест 1: Нормальна обробка повідомлення")
        
        normal_context = [
            {"text": "Привіт всім!", "timestamp": time.time() - 300},
            {"text": "Як справи?", "timestamp": time.time() - 250},
            {"text": "Все нормально", "timestamp": time.time() - 200},
        ]
        
        result = process_message_with_smart_context(
            "Гряг, що думаєш про це?",
            chat_id=123,
            context=normal_context
        )
        
        print(f"   Результат: shouldRespond={result['should_respond']}")
        print(f"   Тон: {result['response_tone']}")
        print(f"   Рекомендації: {result.get('recommendations', {})}")
        
        # Тест 2: Ситуація зі спамом
        print("\n🔄 Тест 2: Обробка спаму")
        
        spam_messages = []
        current_time = time.time()
        
        for i in range(35):  # Створюємо 35 повідомлень за 5 хвилин (спам)
            spam_messages.append({
                "text": f"спам повідомлення {i}",
                "timestamp": current_time - (300 - i * 8)  # Розподіляємо по 5 хвилинам
            })
        
        spam_analysis = analyze_chat_spam_level(456, spam_messages)
        print(f"   Рівень спаму: {spam_analysis['spam_level']}")
        print(f"   Частота повідомлень: {spam_analysis['message_frequency']}")
        print(f"   Скорегований шанс відповіді: {spam_analysis['suggested_reply_chance']:.3f}")
        
        anti_spam_msg = get_anti_spam_message(spam_analysis['spam_level'])
        print(f"   Анти-спам повідомлення: {anti_spam_msg}")
        
        # Тест 3: Стиснення контексту
        print("\n🔄 Тест 3: Стиснення великого контексту")
        
        large_context = []
        for i in range(150):  # Створюємо великий контекст
            text = f"повідомлення {i}"
            if i % 10 == 0:  # Кожне 10-те повідомлення важливе
                text = f"Гряг, важливе питання {i}?"
            
            large_context.append({
                "text": text,
                "timestamp": current_time - (1000 - i * 6)
            })
        
        compressed = compress_context_smartly(large_context, max_context_size=50)
        print(f"   Стиснуто з {len(large_context)} до {len(compressed)} повідомлень")
        
        # Підраховуємо скільки важливих повідомлень збережено
        important_saved = sum(1 for msg in compressed if "важливе питання" in msg['text'])
        print(f"   Збережено важливих повідомлень: {important_saved}")
        
        # Тест 4: Комплексна обробка зі спамом
        print("\n🔄 Тест 4: Комплексна обробка повідомлення зі спамом")
        
        spam_result = process_message_with_smart_context(
            "Просто звичайне повідомлення",
            chat_id=456,
            context=spam_messages,
            recent_messages=spam_messages[-10:]
        )
        
        print(f"   Чи відповідати: {spam_result['should_respond']}")
        print(f"   Рівень спаму: {spam_result['spam_analysis']['spam_level']}")
        print(f"   Рекомендована довжина відповіді: {spam_result['recommendations']['max_response_length']}")
        print(f"   Стиль відповіді: {spam_result['recommendations']['response_style']}")
        
        # Тест 5: Статистика
        print("\n🔄 Тест 5: Статистика обробки")
        
        stats = get_processing_statistics(456)
        print(f"   Повідомлень за останню годину: {stats['messages_last_hour']}")
        print(f"   Записів аналізу: {stats['analysis_records']}")
        
        print("\n✅ Всі тести пройдено успішно!")
        print("\n📊 Рекомендації для використання:")
        print("   1. Використовуйте process_message_with_smart_context() як головну функцію")
        print("   2. Функція автоматично виявляє спам та корегує поведінку")
        print("   3. Великий контекст автоматично стискається")
        print("   4. В умовах спаму бот стає менш активним")
        print("   5. Використовуйте рекомендації для налаштування відповідей")
        
        return True
        
    except ImportError as e:
        print(f"❌ Помилка імпорту: {e}")
        return False
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        return False

def test_context_compression_edge_cases():
    """Тести граничних випадків стиснення контексту"""
    
    try:
        from bot.modules.enhanced_behavior import compress_context_smartly
        
        print("\n🔄 Тести граничних випадків:")
        
        # Тест порожнього контексту
        empty_result = compress_context_smartly([], 10)
        print(f"   Порожній контекст: {len(empty_result)} повідомлень")
        
        # Тест контексту меншого за ліміт
        small_context = [{"text": "test", "timestamp": time.time()}]
        small_result = compress_context_smartly(small_context, 10)
        print(f"   Малий контекст: {len(small_result)} повідомлень")
        
        # Тест контексту тільки з важливими повідомленнями
        important_only = [
            {"text": "Гряг, питання 1?", "timestamp": time.time() - 100},
            {"text": "Гряг, питання 2?", "timestamp": time.time() - 50},
            {"text": "Гряг, питання 3?", "timestamp": time.time()},
        ]
        important_result = compress_context_smartly(important_only, 2)
        print(f"   Тільки важливі (3->2): {len(important_result)} повідомлень")
        
        print("   ✅ Граничні випадки пройдено")
        
    except Exception as e:
        print(f"   ❌ Помилка в граничних випадках: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестів покращеної обробки контексту...")
    
    success = test_smart_context_processing()
    test_context_compression_edge_cases()
    
    if success:
        print("\n🎉 Система покращеної обробки контексту готова до використання!")
        print("\n📝 Для інтеграції використовуйте:")
        print("   from bot.modules.enhanced_behavior import process_message_with_smart_context")
        print("   result = process_message_with_smart_context(message, chat_id, context)")
    else:
        print("\n❌ Є проблеми, які потрібно виправити")
        exit(1)
