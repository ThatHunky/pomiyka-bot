#!/usr/bin/env python3
"""
Startup script для Гряг-бота з покращеннями Фази 1
"""
import sys
import os
import asyncio
import logging
from datetime import datetime

# Додаємо шлях до проєкту
sys.path.insert(0, os.path.dirname(__file__))

print("🚀 Гряг-бот v3.0 - Запуск з покращеннями...")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Перевіряємо .env
if not os.path.exists('.env'):
    print("❌ Файл .env не знайдено!")
    print("📋 Скопіюйте .env.sample як .env та заповніть токени:")
    print("   cp .env.sample .env")
    # Генеруємо .env.sample автоматично
    try:
        from bot.modules.config_validator import ConfigValidator
        ConfigValidator().generate_env_sample()
        print("✅ Створено .env.sample")
    except Exception as e:
        print(f"⚠️  Не вдалося створити .env.sample: {e}")
    sys.exit(1)

# Перевіряємо залежності
try:
    import aiogram
    import aiohttp
    import aiosqlite
    from dotenv import load_dotenv
    load_dotenv()
except ImportError as e:
    print(f"❌ Не вистачає залежностей: {e}")
    print("📦 Встановіть залежності:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# 🔧 Валідація конфігурації (Фаза 1)
print("🔧 Валідація конфігурації...")
try:
    from bot.modules.config_validator import ConfigValidator
    validator = ConfigValidator()
    if not validator.validate_all():
        print("❌ Конфігурація містить помилки!")
        sys.exit(1)
    print("✅ Конфігурація валідна")
except Exception as e:
    print(f"⚠️  Помилка валідації конфігурації: {e}")

# 📊 Ініціалізація моніторингу (Фаза 1)
print("📊 Ініціалізація системи моніторингу...")
try:
    from bot.modules.performance_monitor import PerformanceMonitor
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    print("✅ Моніторинг активний")
except Exception as e:
    print(f"⚠️  Помилка ініціалізації моніторингу: {e}")

# 🔄 Ініціалізація асинхронної БД (Фаза 1)
print("🔄 Ініціалізація асинхронної бази даних...")
try:
    from bot.modules.context_async import AsyncContextManager
    async def init_async_db():
        async_db = AsyncContextManager()
        await async_db.initialize()
        return async_db
    
    # Тестуємо з'єднання
    asyncio.run(init_async_db())
    print("✅ Асинхронна БД готова")
except Exception as e:
    print(f"⚠️  Помилка асинхронної БД: {e}")

# 💾 Ініціалізація кешу Gemini (Фаза 1)
print("💾 Ініціалізація кешу Gemini...")
try:
    from bot.modules.gemini_cache import GeminiCache
    cache = GeminiCache()
    cache.cleanup_expired()
    stats = cache.get_stats()
    print(f"✅ Кеш готовий (записів: {stats['total_entries']})")
except Exception as e:
    print(f"⚠️  Помилка ініціалізації кешу: {e}")

# 💾 Автоматичний backup при старті
print("💾 Створення резервної копії...")
try:
    from bot.modules.backup_manager import backup_database
    backup_database()
    print("✅ Backup створено")
except Exception as e:
    print(f"⚠️  Не вдалося створити резервну копію: {e}")

# 🏥 Перевірка здоров'я системи
print("🏥 Перевірка здоров'я системи...")
try:
    from bot.modules.performance_monitor import PerformanceMonitor
    monitor = PerformanceMonitor()
    health = monitor.health_check()
    if health['status'] == 'healthy':
        print("✅ Система здорова")
    else:
        print(f"⚠️  Проблеми зі здоров'ям: {health}")
except Exception as e:
    print(f"⚠️  Помилка перевірки здоров'я: {e}")

print("🎯 Всі системи готові! Запускаю бота...")

# Запускаємо бота
if __name__ == "__main__":
    try:
        from bot.main import main
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Гряг йде спати...")
        # Graceful shutdown
        try:
            from bot.modules.performance_monitor import PerformanceMonitor
            monitor = PerformanceMonitor()
            monitor.stop_monitoring()
            print("✅ Моніторинг зупинено")
        except:
            pass
    except Exception as e:
        print(f"💥 Критична помилка: {e}")
        logging.exception("Критична помилка:")
        sys.exit(1)
