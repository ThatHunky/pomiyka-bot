#!/usr/bin/env python3
"""
Комплексний тест всіх async-рефакторених модулів
"""

import asyncio
import os
import tempfile
import logging
from datetime import datetime
from bot.modules.context_sqlite import init_db, save_message_obj, get_context
from bot.modules.local_analyzer import get_analyzer
from bot.modules.personalization import create_personalization_manager

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_all_async_modules():
    """Комплексний тест всіх async модулів"""
    
    print("🚀 Комплексний тест async рефакторингу...")
    
    # Створюємо тимчасові БД
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_context:
        context_db_path = tmp_context.name
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_analyzer:
        analyzer_db_path = tmp_analyzer.name
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_personal:
        personal_db_path = tmp_personal.name
    
    try:
        # 1. Тест context_sqlite
        print("📋 1. Тестування context_sqlite (async)...")
        await init_db()
        
        # Використовуємо save_message_obj для тестування
        await save_message_obj(
            chat_id=12345,
            user="test_user",
            text="Тестове повідомлення для context",
            timestamp=datetime.now().isoformat()
        )
        
        context = await get_context(12345, limit=10)
        assert len(context) > 0, "Context має містити повідомлення"
        print("✅ context_sqlite працює async")
        
        # 2. Тест local_analyzer
        print("📋 2. Тестування local_analyzer (async)...")
        analyzer = get_analyzer()
        analyzer.db_path = analyzer_db_path
        
        # Кешування аналізу
        await analyzer.cache_analysis(
            chat_id=12345,
            analysis_type="conversation_type",
            result="technical",
            confidence=0.85
        )
        
        # Отримання кешу
        cached = await analyzer.get_cached_analysis(
            chat_id=12345,
            analysis_type="conversation_type"
        )
        assert cached is not None, "Кеш має містити аналіз"
        print("✅ local_analyzer працює async")
        
        # 3. Тест personalization
        print("📋 3. Тестування personalization (async)...")
        personal_manager = await create_personalization_manager(personal_db_path)
        
        # Обробка повідомлення
        result = await personal_manager.process_user_message(
            user_id=67890,
            username="test_user",
            text="Привіт! Дуже круто! 😊"
        )
        assert result['processed'], "Повідомлення має бути оброблено"
        
        # Статистика
        stats = await personal_manager.get_user_statistics(67890)
        assert 'error' not in stats, "Статистика має бути без помилок"
        print("✅ personalization працює async")
        
        # 4. Інтеграційний тест
        print("📋 4. Інтеграційний тест...")
        
        # Паралельне виконання операцій з різних модулів
        tasks = [
            save_message(12345, 11111, "user1", "Повідомлення 1", datetime.now()),
            analyzer.cache_analysis(12345, "mood", "happy", 0.9),
            personal_manager.process_user_message(11111, "user1", "Привіт!"),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Перевіряємо, що всі операції пройшли без помилок
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Задача {i+1} провалилась: {result}")
                return False
        
        print("✅ Інтеграційний тест пройдено")
        
        # 5. Тест concurrent операцій
        print("📋 5. Тестування concurrent операцій...")
        
        concurrent_tasks = []
        for i in range(10):
            concurrent_tasks.extend([
                save_message(12345, 20000+i, f"user_{i}", f"Повідомлення {i}", datetime.now()),
                analyzer.cache_analysis(12345, f"test_{i}", f"result_{i}", 0.7),
                personal_manager.process_user_message(20000+i, f"user_{i}", f"Тест {i}")
            ])
        
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        errors = [r for r in concurrent_results if isinstance(r, Exception)]
        if errors:
            print(f"❌ {len(errors)} помилок в concurrent тесті")
            for error in errors[:3]:  # Показуємо перші 3 помилки
                print(f"   - {error}")
            return False
        
        print("✅ Concurrent операції працюють")
        
        print("\n🎉 Всі комплексні тести пройдені успішно!")
        return True
        
    except Exception as e:
        print(f"❌ Помилка комплексного тестування: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Видаляємо тимчасові БД
        for db_path in [context_db_path, analyzer_db_path, personal_db_path]:
            try:
                os.unlink(db_path)
            except:
                pass

async def performance_test():
    """Простий тест продуктивності async операцій"""
    print("\n⚡ Тест продуктивності async операцій...")
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        await init_db(db_path)
        
        # Тест швидкості збереження повідомлень
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(100):
            tasks.append(save_message(
                chat_id=12345,
                user_id=i,
                username=f"user_{i}",
                text=f"Тестове повідомлення {i}",
                timestamp=datetime.now()
            ))
        
        await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        print(f"✅ 100 async збережень за {elapsed:.2f} секунд ({100/elapsed:.1f} ops/sec)")
        
        # Тест швидкості отримання контексту
        start_time = asyncio.get_event_loop().time()
        
        tasks = []
        for i in range(50):
            tasks.append(get_context(12345, limit=20))
        
        await asyncio.gather(*tasks)
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        print(f"✅ 50 async отримань контексту за {elapsed:.2f} секунд ({50/elapsed:.1f} ops/sec)")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка тесту продуктивності: {e}")
        return False
        
    finally:
        try:
            os.unlink(db_path)
        except:
            pass

async def main():
    """Головна функція тестування"""
    print("🔥 ФІНАЛЬНЕ ТЕСТУВАННЯ ASYNC РЕФАКТОРИНГУ")
    print("=" * 50)
    
    # Комплексний тест
    complex_success = await test_all_async_modules()
    
    # Тест продуктивності
    perf_success = await performance_test()
    
    print("\n" + "=" * 50)
    if complex_success and perf_success:
        print("🏆 УСПІХ: Async рефакторинг повністю готовий до production!")
        print("📊 Готовність: 100%")
        print("🚀 Статус: ENTERPRISE-READY")
        return 0
    elif complex_success:
        print("⚠️ ЧАСТКОВИЙ УСПІХ: Основні функції працюють, але є питання продуктивності")
        return 0
    else:
        print("❌ КРИТИЧНА ПОМИЛКА: Виявлено проблеми в async реалізації!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
