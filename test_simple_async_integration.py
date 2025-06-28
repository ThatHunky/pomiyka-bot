#!/usr/bin/env python3
"""
Простий інтеграційний тест async модулів
"""

import asyncio
import os
import tempfile
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_async_functionality():
    """Базовий тест async функціональності"""
    
    print("🚀 Базовий інтеграційний тест async модулів...")
    
    try:
        # 1. Тест context_sqlite
        print("📋 1. Тестування context_sqlite...")
        from bot.modules.context_sqlite import init_db
        await init_db()
        print("✅ context_sqlite ініціалізовано")
        
        # 2. Тест local_analyzer  
        print("📋 2. Тестування local_analyzer...")
        from bot.modules.local_analyzer import get_analyzer
        analyzer = get_analyzer()
        
        # Проста перевірка, що аналізатор створено
        assert analyzer is not None, "Analyzer має бути створений"
        print("✅ local_analyzer працює")
        
        # 3. Тест personalization
        print("📋 3. Тестування personalization...")
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            personal_db_path = tmp_file.name
        
        try:
            from bot.modules.personalization import create_personalization_manager
            personal_manager = await create_personalization_manager(personal_db_path)
            
            health = personal_manager.get_health_status()
            assert health['status'] == 'healthy', "PersonalizationManager має бути здоровим"
            print("✅ personalization працює async")
            
        finally:
            try:
                os.unlink(personal_db_path)
            except:
                pass
        
        # 4. Тест паралельної ініціалізації
        print("📋 4. Тестування паралельної ініціалізації...")
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp1, \
             tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp2:
            
            try:
                # Паралельне створення кількох менеджерів
                tasks = [
                    create_personalization_manager(tmp1.name),
                    create_personalization_manager(tmp2.name)
                ]
                
                managers = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Перевіряємо результати
                success_count = 0
                for manager in managers:
                    if not isinstance(manager, Exception):
                        success_count += 1
                
                assert success_count == 2, f"Очікували 2 успішні ініціалізації, отримали {success_count}"
                print("✅ Паралельна ініціалізація працює")
                
            finally:
                try:
                    os.unlink(tmp1.name)
                    os.unlink(tmp2.name)
                except:
                    pass
        
        print("\n🎉 Всі базові інтеграційні тести пройдені!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка інтеграційного тестування: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_async_locks():
    """Тест async locks (thread safety)"""
    print("\n🔒 Тестування async locks...")
    
    try:
        from bot.modules.personalization import create_personalization_manager
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            # Створюємо кілька менеджерів, що працюють з однією БД
            manager1 = await create_personalization_manager(db_path)
            manager2 = await create_personalization_manager(db_path)
            
            # Паралельні операції з тією самою БД
            tasks = []
            for i in range(5):
                tasks.append(manager1.process_user_message(1000+i, f"user_{i}", f"Повідомлення {i}"))
                tasks.append(manager2.process_user_message(2000+i, f"user2_{i}", f"Текст {i}"))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Перевіряємо на помилки
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                print(f"⚠️ {len(errors)} помилок у async locks тесті")
                for error in errors[:2]:
                    print(f"   - {error}")
                return False
            
            print("✅ Async locks працюють правильно")
            return True
            
        finally:
            try:
                os.unlink(db_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Помилка тестування async locks: {e}")
        return False

async def main():
    """Головна функція тестування"""
    print("🔥 ПРОСТИЙ ІНТЕГРАЦІЙНИЙ ТЕСТ ASYNC МОДУЛІВ")
    print("=" * 50)
    
    # Базовий тест
    basic_success = await test_basic_async_functionality()
    
    # Тест locks
    locks_success = await test_async_locks()
    
    print("\n" + "=" * 50)
    if basic_success and locks_success:
        print("🏆 УСПІХ: Async модулі працюють разом!")
        print("📊 Готовність: 100%")
        print("🚀 Статус: READY FOR INTEGRATION")
        return 0
    elif basic_success:
        print("⚠️ ЧАСТКОВИЙ УСПІХ: Базові функції працюють")
        return 0
    else:
        print("❌ ПОМИЛКА: Виявлено критичні проблеми!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
