# EMERGENCY FIX - Основний файл запуску Telegram-бота з виправленнями
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
            
            # Перевірка реакції на бота
            should_respond = False
            bot_name = PERSONA['name'].lower()
            
            if message.text:
                text_lower = message.text.lower()
                # Перевірка згадок бота
                if any(trigger in text_lower for trigger in [bot_name, '@gryag_bot', 'гряг', 'бот']):
                    should_respond = True
                    logging.info(f"Відповідаю на згадку бота: {message.text[:30]}...")
                # Випадковий шанс відповіді
                elif random.random() < PERSONA["smart_reply_chance"]:
                    should_respond = True
                    logging.info(f"Випадкова відповідь: {message.text[:30]}...")
            
            if should_respond:
                try:
                    # Отримуємо контекст
                    chat_context = context.get_recent_messages(chat_id, PERSONA["context_limit"])
                    
                    # 🚨 ПОКРАЩЕНИЙ ПРОМПТ для якісніших відповідей
                    enhanced_instruction = (
                        f"Ти — {PERSONA['name']}, дружелюбний український чат-бот. "
                        "Відповідай природно, коротко та по суті. "
                        "Будь корисним, але не надто серйозним. "
                        "Можеш додати легкий гумор якщо це доречно. "
                        "Не пиши дивних речей або абсурду. "
                        "ВАЖЛИВО: Дай ОДНУ коротку, зрозумілу відповідь українською мовою."
                    )
                    
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
