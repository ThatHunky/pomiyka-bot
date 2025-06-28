#!/usr/bin/env python3
# Простий тест асинхронної БД без connection pool

import asyncio
import os
import sys
import tempfile
import aiosqlite
from pathlib import Path

# Додаємо шлях до модулів бота
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

async def test_simple_async_db():
    """Простий тест асинхронної БД"""
    
    print("🔄 Тестування простої асинхронної БД...")
    
    # Створюємо тимчасову БД
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Підключення до БД
        conn = await aiosqlite.connect(db_path)
        
        # Створення таблиці
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS test_messages (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER,
                message_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Вставка тестових даних
        await conn.execute(
            "INSERT INTO test_messages (chat_id, message_text) VALUES (?, ?)",
            (123, "Тестове повідомлення")
        )
        await conn.commit()
        
        # Читання даних
        async with conn.execute("SELECT * FROM test_messages") as cursor:
            rows = await cursor.fetchall()
            
        print(f"✅ Записано та прочитано {len(rows)} записів")
        
        await conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False
        
    finally:
        # Видаляємо тимчасову БД
        if os.path.exists(db_path):
            os.unlink(db_path)

async def test_context_async_import():
    """Тест імпорту модуля context_async"""
    
    print("🔄 Тестування імпорту context_async...")
    
    try:
        from bot.modules import context_async
        print("✅ Модуль context_async імпортовано успішно")
        
        # Перевіряємо основні функції
        functions = [
            'init_database',
            'add_message_to_context', 
            'get_recent_messages',
            'get_context_summary',
            'get_database_stats'
        ]
        
        for func_name in functions:
            if hasattr(context_async, func_name):
                print(f"✅ Функція {func_name} доступна")
            else:
                print(f"❌ Функція {func_name} відсутня")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка імпорту: {e}")
        return False

async def main():
    """Головна функція тестування"""
    
    print("🚀 ПРОСТИЙ ТЕСТ АСИНХРОННОЇ БД")
    print("=" * 50)
    
    tests = [
        ("Простий тест aiosqlite", test_simple_async_db),
        ("Імпорт context_async", test_context_async_import),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🎯 {test_name}")
        print("-" * 30)
        
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} пройдено")
            else:
                print(f"❌ {test_name} провалено")
        except Exception as e:
            print(f"❌ {test_name} помилка: {e}")
    
    print(f"\n📊 Результат: {passed}/{total} тестів пройдено")
    
    if passed == total:
        print("🎉 Всі тести пройдено успішно!")
        return True
    else:
        print("⚠️ Деякі тести провалено")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
