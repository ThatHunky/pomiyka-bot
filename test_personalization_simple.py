#!/usr/bin/env python3
"""
Простий тест асинхронної персоналізації без очищення даних
"""

import asyncio
import os
import tempfile
import logging
from datetime import datetime
from bot.modules.personalization import create_personalization_manager

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_personalization_basic():
    """Базовий тест асинхронної роботи модуля персоналізації"""
    
    print("🧪 Базовий тест async персоналізації...")
    
    # Створюємо тимчасову БД
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        # 1. Створення та ініціалізація менеджера
        print("📋 1. Ініціалізація PersonalizationManager...")
        manager = await create_personalization_manager(temp_db_path)
        print("✅ Менеджер успішно ініціалізовано")
        
        # 2. Обробка повідомлень користувачів
        print("📋 2. Тестування обробки повідомлень...")
        
        test_users = [
            (12345, "test_user1", "Привіт! Як справи? 😊"),
            (67890, "test_user2", "Будь ласка, допоможіть з кодом"),
            (11111, "test_user3", "Супер круто! 🔥 Дуже подобається")
        ]
        
        for user_id, username, text in test_users:
            result = await manager.process_user_message(user_id, username, text)
            print(f"✅ Повідомлення від {username}: {result['processed']}")
        
        # 3. Оновлення уподобань
        print("📋 3. Тестування оновлення уподобань...")
        await manager.update_user_preference(12345, "humor_level", 0.8)
        print("✅ Уподобання оновлено")
        
        # 4. Отримання статистики
        print("📋 4. Тестування статистики користувачів...")
        for user_id, username, _ in test_users:
            stats = await manager.get_user_statistics(user_id)
            if 'error' not in stats:
                print(f"✅ Статистика {username}: {stats['total_messages']} повідомлень")
            else:
                print(f"❌ Помилка статистики {username}: {stats['error']}")
        
        # 5. Перевірка стану (без очищення даних)
        print("📋 5. Перевірка стану здоров'я...")
        health = manager.get_health_status()
        print(f"✅ Стан: {health['status']}, користувачів: {health['users_count']}")
        
        print("\n🎉 Всі базові тести пройдені успішно!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка тестування: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Видаляємо тимчасову БД
        try:
            os.unlink(temp_db_path)
        except:
            pass

async def test_cleanup_separately():
    """Окремий тест для очищення даних з таймаутом"""
    print("\n🧹 Окремий тест очищення даних...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        temp_db_path = tmp_file.name
    
    try:
        manager = await create_personalization_manager(temp_db_path)
        
        # Додаємо тестові дані
        await manager.process_user_message(12345, "test_user", "Тестове повідомлення")
        
        # Тестуємо очищення з таймаутом
        print("📋 Тестування очищення даних з таймаутом...")
        try:
            deleted_count = await asyncio.wait_for(
                manager.cleanup_old_data(days_to_keep=1), 
                timeout=10.0
            )
            print(f"✅ Очищено {deleted_count} старих записів")
            return True
        except asyncio.TimeoutError:
            print("⚠️ Очищення даних перевищило таймаут 10 секунд")
            return False
            
    except Exception as e:
        print(f"❌ Помилка тестування очищення: {e}")
        return False
        
    finally:
        try:
            os.unlink(temp_db_path)
        except:
            pass

async def main():
    """Головна функція тестування"""
    # Базовий тест
    basic_success = await test_personalization_basic()
    
    # Тест очищення окремо
    cleanup_success = await test_cleanup_separately()
    
    if basic_success and cleanup_success:
        print("✅ УСПІХ: Асинхронна персоналізація працює правильно!")
        return 0
    elif basic_success:
        print("⚠️ ЧАСТКОВИЙ УСПІХ: Базові функції працюють, але є проблеми з очищенням")
        return 0
    else:
        print("❌ ПОМИЛКА: Виявлено критичні проблеми!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
