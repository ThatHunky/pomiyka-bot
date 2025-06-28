#!/usr/bin/env python3
"""
🚨 EMERGENCY FIX для Гряг-бота - виправлення критичних проблем
Виправляє: спам старими повідомленнями + поліпшує якість відповідей
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone, timedelta
import logging

def create_emergency_main():
    """Створює emergency версію main.py з критичними виправленнями"""
    emergency_main_content = '''# EMERGENCY FIX - Основний файл запуску Telegram-бота з виправленнями
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
import asyncio
import logging
from bot.modules import context, gemini, management, media_map, random_life, smart_behavior, chat_scanner, reactions, rate_limiter, enhanced_behavior
from bot.bot_config import PERSONA
import os
from dotenv import load_dotenv
import random
from datetime import datetime, timezone, timedelta
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from typing import Optional, Dict, Any
import signal

# Час запуску бота для ігнорування старих повідомлень - КРИТИЧНО!
BOT_START_TIME = datetime.now(timezone.utc)

load_dotenv()

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not API_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не знайдено в змінних середовища")

logging.basicConfig(level=logging.INFO)

# Глобальний бот
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def validate_config() -> None:
    """Перевіряє наявність критичних змінних середовища."""
    required_vars = ["TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Відсутні обов'язкові змінні: {', '.join(missing)}")

validate_config()

def is_message_too_old(message: Message) -> bool:
    """🚨 КРИТИЧНЕ ВИПРАВЛЕННЯ: Перевіряє чи повідомлення створене до запуску бота"""
    if not PERSONA["ignore_old_messages"]:
        return False
    if not message.date:
        return False
    
    # Конвертуємо message_time у UTC якщо потрібно
    message_time = message.date
    if message_time.tzinfo is None:
        message_time = message_time.replace(tzinfo=timezone.utc)
    
    # Повідомлення старе, якщо воно було створене ДО запуску бота
    # Буферна зона 30 секунд для часових розбіжностей
    buffer_zone = timedelta(seconds=30)
    cutoff_time = BOT_START_TIME - buffer_zone
    
    if message_time < cutoff_time:
        # Не логуємо кожне старе повідомлення, щоб не засмічувати логи
        return True
    
    return False

async def safe_reply(message: Message, text: str) -> bool:
    """Безпечна відправка відповіді з обробкою помилок"""
    try:
        await message.reply(text)
        return True
    except TelegramRetryAfter as e:
        logging.warning(f"Telegram rate limit: затримка {e.retry_after} секунд")
        return False
    except TelegramBadRequest as e:
        logging.warning(f"Telegram помилка: {e}")
        return False
    except Exception as e:
        logging.error(f"Несподівана помилка при відправці: {e}")
        return False

# Обробка старту
@dp.message(CommandStart())
async def start_handler(message: Message) -> None:
    """Вітальний хендлер"""
    await message.answer(f"Вітаю! Я {PERSONA['name']}. {PERSONA['description']}")

# 🚨 КРИТИЧНЕ ВИПРАВЛЕННЯ: Спрощений хендлер без спаму
@dp.message()
async def universal_handler(message: Message) -> None:
    """Універсальний хендлер для всіх повідомлень - EMERGENCY VERSION"""
    try:
        # 🚨 КРИТИЧНО: Ігноруємо старі повідомлення
        if is_message_too_old(message):
            return
        
        # Перевірка None для from_user
        if not message.from_user or not getattr(message.from_user, 'id', None):
            logging.warning("message.from_user відсутній, ігноруємо повідомлення")
            return
        
        # Логуємо тільки нові повідомлення
        user_name = message.from_user.full_name or "Невідомий"
        if message.text and len(message.text) > 10:
            logging.info(f"🆕 Нове повідомлення від {user_name}: {message.text[:50]}...")
        else:
            logging.info(f"🆕 Нове повідомлення від {user_name}: {message.text or '[медіа]'}")
        
        # Адмін-команди (пріоритет)
        if message.from_user.id == PERSONA["admin_id"]:
            if message.text and message.text.startswith("/"):
                management.handle(message)
                return
        
        # Групові чати
        if message.chat.type in ["group", "supergroup"]:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Rate limiting
            if not rate_limiter.rate_limiter.can_send_message(
                chat_id,
                PERSONA["rate_limit_per_chat"],
                PERSONA["global_rate_limit"]
            ):
                logging.info(f"Rate limit: пропускаємо відповідь в чат {chat_id}")
                return
            
            # Збереження в контексті
            context.add_message(chat_id, user_id, message.text or "[медіа]", user_name)
            
            # Перевірка реакції на бота - ПОКРАЩЕНО з підтримкою reply_to_message
            should_respond = False
            bot_name = PERSONA['name'].lower()
            is_reply_to_bot = False
            
            # Перевірка чи це відповідь на повідомлення бота
            if message.reply_to_message and message.reply_to_message.from_user:
                if message.reply_to_message.from_user.id == bot.id:
                    is_reply_to_bot = True
                    should_respond = True  # Завжди відповідаємо на прямі відповіді
                    logging.info(f"🔗 Відповідь на бота від {user_name}: {message.text[:30]}...")
            
            if not should_respond and message.text:
                text_lower = message.text.lower()
                # Перевірка згадок бота
                if any(trigger in text_lower for trigger in [bot_name, '@gryag_bot', 'гряг', 'бот']):
                    should_respond = True
                    logging.info(f"📢 Згадка бота від {user_name}: {message.text[:30]}...")
                # Збільшений випадковий шанс відповіді
                elif random.random() < PERSONA["smart_reply_chance"]:  # Тепер 15% замість 3%
                    should_respond = True
                    logging.info(f"🎲 Випадкова відповідь ({PERSONA['smart_reply_chance']*100:.1f}%): {message.text[:30]}...")
            
            if should_respond:
                try:
                    # Отримуємо контекст
                    chat_context = context.get_recent_messages(chat_id, PERSONA["context_limit"])
                    
                    # 🚨 ПОКРАЩЕНИЙ ПРОМПТ з підтримкою діалогового контексту
                    enhanced_instruction = (
                        f"Ти — {PERSONA['name']}, дружелюбний український чат-бот. "
                        "Відповідай природно, коротко та по суті. "
                        "Будь корисним, але не надто серйозним. "
                        "Можеш додати легкий гумор якщо це доречно. "
                        "Не пиши дивних речей або абсурду. "
                    )
                    
                    # Додаткові інструкції для відповідей на бота
                    if is_reply_to_bot:
                        enhanced_instruction += (
                            "ВАЖЛИВО: Користувач відповідає на твоє попереднє повідомлення. "
                            "Підтримай діалог і дай релевантну відповідь на їхню репліку. "
                        )
                    
                    enhanced_instruction += "ВАЖЛИВО: Дай ОДНУ коротку, зрозумілу відповідь українською мовою."
                    
                    # Обробка повідомлення через Gemini
                    reply = await gemini.process_message(message, enhanced_instruction)
                    
                    if reply and len(reply.strip()) > 0:
                        await safe_reply(message, reply)
                        logging.info(f"✅ Відправлено відповідь: {reply[:50]}...")
                    else:
                        logging.warning("Gemini повернув порожню відповідь")
                        
                except Exception as e:
                    logging.error(f"Помилка в universal_handler: {e}")
                    await safe_reply(message, "Ой, щось пішло не так... 🤖")
            
            # Реакції (незалежно від відповідей)
            try:
                await reactions.maybe_react_to_message(message)
            except Exception as e:
                logging.error(f"Помилка при додаванні реакції: {e}")
            
        # Приватні чати
        elif message.chat.type == "private":
            try:
                # Збереження в контексті
                if message.from_user:
                    context.add_message(message.chat.id, message.from_user.id, 
                                      message.text or "[медіа]", user_name)
                
                # Завжди відповідаємо в приватних чатах
                chat_context = context.get_recent_messages(message.chat.id, PERSONA["context_limit"])
                
                enhanced_instruction = (
                    f"Ти — {PERSONA['name']}, дружелюбний український чат-бот. "
                    "Це приватна розмова, тому будь більш особистим та уважним. "
                    "Відповідай корисно та природно. "
                    "Дай ОДНУ змістовну відповідь українською мовою."
                )
                
                reply = await gemini.process_message(message, enhanced_instruction)
                
                if reply and len(reply.strip()) > 0:
                    await safe_reply(message, reply)
                    logging.info(f"✅ Приватна відповідь: {reply[:50]}...")
                else:
                    await safe_reply(message, "Можу допомогти з чимось? 🤖")
                    
            except Exception as e:
                logging.error(f"Помилка в приватному чаті: {e}")
                await safe_reply(message, "Вибачте, сталася помилка... 🤖")
        
    except Exception as e:
        logging.error(f"Критична помилка в universal_handler: {e}")

async def main() -> None:
    """Головна точка входу - EMERGENCY VERSION"""
    
    print("🚨 EMERGENCY FIX - Запускаю Гряг-бота...")
    print(f"⏰ Час запуску: {BOT_START_TIME}")
    print(f"🛡️ Ігнорування старих повідомлень: {PERSONA['ignore_old_messages']}")
    print("🔧 Версія: Emergency Fix для спаму старими повідомленнями")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Критична помилка: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Записуємо emergency версію
    emergency_path = "bot/main_emergency.py"
    with open(emergency_path, 'w', encoding='utf-8') as f:
        f.write(emergency_main_content)
    
    print(f"✅ Створено emergency версію: {emergency_path}")
    return emergency_path

def create_emergency_docker_compose():
    """Створює emergency docker-compose для швидкого фіксу"""
    emergency_compose = '''version: '3.8'

services:
  gryag-bot-emergency:
    build: .
    container_name: gryag-bot-emergency-fix
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - BOT_IGNORE_OLD_MESSAGES=true
      - BOT_MAX_MESSAGE_AGE_MINUTES=10
      - GEMINI_MODEL=gemini-2.5-flash
      - GEMINI_API_VERSION=v1
    command: python -m bot.main_emergency
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
'''
    
    emergency_compose_path = "docker-compose.emergency.yml"
    with open(emergency_compose_path, 'w', encoding='utf-8') as f:
        f.write(emergency_compose)
    
    print(f"✅ Створено emergency compose: {emergency_compose_path}")
    return emergency_compose_path

def create_emergency_env():
    """Створює правильний .env для emergency fix"""
    emergency_env = '''# EMERGENCY FIX CONFIGURATION
# Критичні виправлення для спаму старими повідомленнями

# === BASIC ===
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
BOT_ADMIN_ID=your_telegram_user_id

# === CRITICAL FIX ===
BOT_IGNORE_OLD_MESSAGES=true
BOT_MAX_MESSAGE_AGE_MINUTES=10

# === GEMINI (ВИПРАВЛЕНА МОДЕЛЬ) ===
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_VERSION=v1
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=200

# === RATE LIMITING ===
BOT_RATE_LIMIT_PER_CHAT=3
BOT_GLOBAL_RATE_LIMIT=20
BOT_SMART_REPLY_CHANCE=0.05

# === CONTEXT ===
BOT_CONTEXT_LIMIT=50
BOT_MAX_CONTEXT_TOKENS=800000

# === PERSONA ===
BOT_NAME=Гряг
BOT_DESCRIPTION=Дружелюбний український чат-бот
'''
    
    emergency_env_path = ".env.emergency"
    with open(emergency_env_path, 'w', encoding='utf-8') as f:
        f.write(emergency_env)
    
    print(f"✅ Створено emergency .env: {emergency_env_path}")
    return emergency_env_path

def main():
    """Основна функція emergency fix"""
    print("🚨" + "="*60 + "🚨")
    print("   EMERGENCY FIX для Гряг-бота v3.2")
    print("   Виправляє критичні проблеми:")
    print("   1. Спам старими повідомленнями при запуску")
    print("   2. Поліпшує якість відповідей")
    print("   3. Виправляє модель Gemini")
    print("🚨" + "="*60 + "🚨")
    
    try:
        # Створюємо emergency файли
        emergency_main = create_emergency_main()
        emergency_compose = create_emergency_docker_compose()
        emergency_env = create_emergency_env()
        
        print("\n🔧 EMERGENCY FIX готовий!")
        print("\n📋 ШВИДКІ ІНСТРУКЦІЇ:")
        print("1. Зупиніть поточний бот:")
        print("   docker-compose down")
        
        print("\n2. Скопіюйте налаштування:")
        print(f"   cp {emergency_env} .env")
        print("   # Відредагуйте .env з вашими токенами!")
        
        print("\n3. Запустіть emergency версію:")
        print(f"   docker-compose -f {emergency_compose} up -d")
        
        print("\n4. Перегляньте логи:")
        print("   docker-compose -f docker-compose.emergency.yml logs -f")
        
        print("\n✅ РЕЗУЛЬТАТ:")
        print("- ❌ НЕ БУДЕ спаму старими повідомленнями")
        print("- ✅ БУДЕ ігнорувати повідомлення до запуску бота")
        print("- ✅ БУДЕ якісніші відповіді з Gemini 2.5 Flash")
        print("- ✅ БУДЕ поліпшені промпти")
        
        print(f"\n📁 Створені файли:")
        print(f"   - {emergency_main}")
        print(f"   - {emergency_compose}")
        print(f"   - {emergency_env}")
        
        print("\n🚨 ВАЖЛИВО: Не забудьте відредагувати .env з вашими токенами!")
        
    except Exception as e:
        print(f"❌ Помилка створення emergency fix: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
