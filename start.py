#!/usr/bin/env python3
"""
Startup script для Гряг-бота
"""
import sys
import os
import asyncio
import logging

# Додаємо шлях до проєкту
sys.path.insert(0, os.path.dirname(__file__))

# Перевіряємо .env
if not os.path.exists('.env'):
    print("❌ Файл .env не знайдено!")
    print("📋 Скопіюйте .env.sample як .env та заповніть токени:")
    print("   cp .env.sample .env")
    sys.exit(1)

# Перевіряємо залежності
try:
    import aiogram
    import aiohttp
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Не вистачає залежностей: {e}")
    print("📦 Встановіть залежності:")
    print("   pip install -r requirements.txt")
    sys.exit(1)

# Автоматичний backup при старті
try:
    from bot.modules.backup_manager import backup_database
    backup_database()
except Exception as e:
    print(f"[WARN] Не вдалося створити резервну копію при старті: {e}")

# Запускаємо бота
if __name__ == "__main__":
    print("🤖 Запускаю Гряг-бота...")
    try:
        from bot.main import main
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Гряг йде спати...")
    except Exception as e:
        print(f"💥 Критична помилка: {e}")
        logging.exception("Критична помилка:")
        sys.exit(1)
