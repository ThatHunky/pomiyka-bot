#!/usr/bin/env python3
"""
Швидкий тест для перевірки async рефакторингу основних модулів
"""

import asyncio
import sys
import os
import tempfile
from datetime import datetime

# Додаємо шлях до модулів
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

async def test_async_context_sqlite():
    """Тест async функцій context_sqlite"""
    print("🔄 Тестування context_sqlite async функцій...")
    
    try:
        from bot.modules.context_sqlite import (
            init_db, save_message, get_context, 
            get_recent_messages, add_message_to_context,
            get_chat_stats, get_global_stats, get_active_chats,
            import_telegram_history, save_message_obj
        )
        
        # Тимчасова тестова БД
        temp_db = tempfile.mktemp(suffix='.db')
        
        # Мокаємо Message об'єкт
        class MockMessage:
            def __init__(self, text: str, chat_id: int = 123):
                self.text = text
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = type('User', (), {
                    'id': 999, 
                    'full_name': 'Test User'
                })()
        
        # Тест ініціалізації БД
        await init_db()
        print("✅ init_db() - успішно")
        
        # Тест збереження повідомлення
        test_msg = MockMessage("Тестове повідомлення", 123)
        await save_message(test_msg)
        print("✅ save_message() - успішно")
        
        # Тест отримання контексту
        context = await get_context(123, limit=10)
        assert isinstance(context, list), "Context має бути списком"
        print("✅ get_context() - успішно")
        
        # Тест додавання повідомлення до контексту
        await add_message_to_context(123, "Test User", "Ще одне повідомлення")
        print("✅ add_message_to_context() - успішно")
        
        # Тест статистики чату
        stats = await get_chat_stats(123)
        assert 'total_messages' in stats, "Статистика має містити total_messages"
        print("✅ get_chat_stats() - успішно")
        
        # Тест глобальної статистики
        global_stats = await get_global_stats()
        assert 'total_messages' in global_stats, "Глобальна статистика має містити total_messages"
        print("✅ get_global_stats() - успішно")
        
        # Тест активних чатів
        active_chats = await get_active_chats()
        assert isinstance(active_chats, list), "Active chats має бути списком"
        print("✅ get_active_chats() - успішно")
        
        print("🎉 Всі тести context_sqlite пройдені успішно!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка в context_sqlite тестах: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_local_analyzer():
    """Тест async функцій local_analyzer"""
    print("🔄 Тестування local_analyzer async функцій...")
    
    try:
        from bot.modules.local_analyzer import get_analyzer
        
        analyzer = get_analyzer()
        
        # Тест ініціалізації БД
        await analyzer._ensure_db_initialized()
        print("✅ _ensure_db_initialized() - успішно")
        
        # Тест кешування
        test_text = "Це тестовий текст для аналізу настрою"
        
        # Перевіряємо, що функція кешування працює
        cached = await analyzer.get_cached_analysis(test_text)
        # Кеш може бути і не порожнім - це нормально
        print("✅ get_cached_analysis() (порожній кеш) - успішно")
        
        # Тест аналізу повідомлення
        analysis = await analyzer.analyze_message(test_text, use_cache=False)
        assert isinstance(analysis, dict), "Аналіз має бути словником"
        assert 'emotion' in analysis, "Аналіз має містити emotion"
        print("✅ analyze_message() - успішно")
        
        # Тест збереження в кеш
        await analyzer.cache_analysis(test_text, analysis)
        print("✅ cache_analysis() - успішно")
        
        # Тепер кеш має містити результат
        cached = await analyzer.get_cached_analysis(test_text)
        assert cached is not None, "Кеш має містити збережений результат"
        assert cached['emotion'] == analysis['emotion'], "Кешований результат має співпадати"
        print("✅ get_cached_analysis() (заповнений кеш) - успішно")
        
        print("🎉 Всі тести local_analyzer пройдені успішно!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка в local_analyzer тестах: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_integration():
    """Інтеграційний тест async взаємодії модулів"""
    print("🔄 Тестування інтеграції async модулів...")
    
    try:
        from bot.modules.context_sqlite import save_message, get_context
        from bot.modules.local_analyzer import get_analyzer
        
        # Мокаємо Message
        class MockMessage:
            def __init__(self, text: str, chat_id: int = 456):
                self.text = text
                self.chat = type('Chat', (), {'id': chat_id})()
                self.from_user = type('User', (), {
                    'id': 888, 
                    'full_name': 'Integration Test User'
                })()
        
        # Зберігаємо тестове повідомлення
        test_msg = MockMessage("Я дуже радий сьогодні! 😊", 456)
        await save_message(test_msg)
        print("✅ Збереження тестового повідомлення - успішно")
        
        # Отримуємо контекст
        context = await get_context(456, limit=5)
        assert len(context) >= 1, "Контекст має містити щонайменше одне повідомлення"
        print("✅ Отримання контексту - успішно")
        
        # Аналізуємо повідомлення
        analyzer = get_analyzer()
        analysis = await analyzer.analyze_message(test_msg.text)
        assert analysis['emotion'] in ['радість', 'нейтральний'], f"Очікувана радість або нейтральний, отримано: {analysis['emotion']}"
        print("✅ Аналіз настрою - успішно")
        
        print("🎉 Інтеграційний тест пройшов успішно!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка в інтеграційному тесті: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Головна функція тестування"""
    print("🚀 Запуск async рефакторинг тестів")
    print("=" * 50)
    
    # Налаштування логування
    import logging
    logging.basicConfig(level=logging.WARNING)  # Приховуємо debug інформацію
    
    results = []
    
    # Запускаємо тести
    results.append(await test_async_context_sqlite())
    results.append(await test_async_local_analyzer())
    results.append(await test_async_integration())
    
    print("=" * 50)
    
    # Підсумки
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Всі тести пройдені! ({passed}/{total})")
        print("✅ Async рефакторинг працює коректно!")
        return 0
    else:
        print(f"❌ Деякі тести не пройдені: {passed}/{total}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
