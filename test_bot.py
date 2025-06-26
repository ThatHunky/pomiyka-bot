#!/usr/bin/env python3
"""
Тест скрипт для перевірки базових функцій бота
"""
import sys
import os
import tempfile

# Додаємо шлях до проєкту
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Тестуємо імпорти всіх модулів"""
    try:
        from bot.modules import context, gemini, management, media_map, random_life, smart_behavior, chat_scanner
        from bot.modules.context_sqlite import init_db, get_global_stats
        from bot.bot_config import PERSONA
        print("✅ Всі модулі імпортуються успішно")
        return True
    except Exception as e:
        print(f"❌ Помилка імпорту: {e}")
        return False

def test_database():
    """Тестуємо роботу бази даних"""
    try:
        # Створюємо тимчасову базу
        original_db = os.environ.get("BOT_DATA_DIR")
        temp_dir = tempfile.mkdtemp()
        os.environ["BOT_DATA_DIR"] = temp_dir
        
        from bot.modules.context_sqlite import init_db, save_message_obj, get_global_stats
        
        # Ініціалізуємо базу
        init_db()
        
        # Додаємо тестове повідомлення  
        save_message_obj(
            chat_id=-1001234567890,
            user="Test User",
            text="Тестове повідомлення",
            timestamp="2025-01-01T12:00:00"
        )
        
        # Перевіряємо статистику
        stats = get_global_stats()
        assert stats["total_messages"] == 1
        assert stats["active_chats"] == 1
        
        print("✅ База даних працює правильно")
        
        # Відновлюємо оригінальні налаштування
        if original_db:
            os.environ["BOT_DATA_DIR"] = original_db
        else:
            del os.environ["BOT_DATA_DIR"]
            
        return True
    except Exception as e:
        print(f"❌ Помилка тестування бази: {e}")
        return False

def test_chat_scanner():
    """Тестуємо модуль сканування чатів"""
    try:
        from bot.modules.chat_scanner import is_chat_scanned, mark_chat_scanned
        
        test_chat_id = -1001111111111
        
        # Спочатку чат не сканований
        assert not is_chat_scanned(test_chat_id)
        
        # Позначаємо як сканований
        mark_chat_scanned(test_chat_id)
        
        # Тепер має бути сканований
        assert is_chat_scanned(test_chat_id)
        
        print("✅ Модуль сканування чатів працює")
        return True
    except Exception as e:
        print(f"❌ Помилка тестування chat_scanner: {e}")
        return False

def test_config():
    """Тестуємо конфігурацію"""
    try:
        from bot.bot_config import PERSONA, DB_PATH, MEDIA_MAP_PATH, CHAT_STATE_PATH
        
        # Перевіряємо основні параметри
        assert "name" in PERSONA
        assert "auto_scan_history" in PERSONA
        assert "max_history_scan" in PERSONA
        
        # Перевіряємо шляхи
        assert DB_PATH.endswith(".db")
        assert MEDIA_MAP_PATH.endswith(".json")
        assert CHAT_STATE_PATH.endswith(".json")
        
        print("✅ Конфігурація правильна")
        return True
    except Exception as e:
        print(f"❌ Помилка тестування конфігурації: {e}")
        return False

def main():
    print("🧪 Початок тестування Гряг-бота...\n")
    
    tests = [
        ("Імпорти модулів", test_imports),
        ("База даних", test_database), 
        ("Сканування чатів", test_chat_scanner),
        ("Конфігурація", test_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 Тестую: {test_name}")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Результат: {passed}/{total} тестів пройдено")
    
    if passed == total:
        print("🎉 Всі тести пройдено! Бот готовий до роботи.")
        return 0
    else:
        print("⚠️ Деякі тести не пройдено. Перевірте налаштування.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
