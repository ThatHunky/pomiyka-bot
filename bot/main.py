# Основний файл запуску Telegram-бота
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

load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# Глобальний бот для доступу з інших модулів (наприклад, /rescan)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def is_message_too_old(message: Message) -> bool:
    """Перевіряє чи повідомлення занадто старе для обробки"""
    if not PERSONA["ignore_old_messages"]:
        return False
    
    if not message.date:
        return False
    
    # Поточний час з урахуванням часової зони
    now = datetime.now(timezone.utc)
    message_time = message.date
    
    # Різниця в хвилинах
    age_minutes = (now - message_time).total_seconds() / 60
    
    if age_minutes > PERSONA["max_message_age_minutes"]:
        logging.info(f"Ігноруємо старе повідомлення (вік: {age_minutes:.1f} хв)")
        return True
    
    return False

async def safe_reply(message: Message, text: str, chat_id = None) -> bool:
    """Безпечна відправка відповіді з rate limiting та error handling"""
    if chat_id is None:
        chat_id = message.chat.id
    
    # Перевірка rate limiting
    if not rate_limiter.rate_limiter.can_send_message(
        chat_id, 
        PERSONA["rate_limit_per_chat"], 
        PERSONA["global_rate_limit"]
    ):
        logging.warning(f"Rate limit: пропускаємо відправку в чат {chat_id}")
        return False
    
    try:
        await message.reply(text)
        return True
    except TelegramRetryAfter as e:
        logging.warning(f"Telegram rate limit: затримка {e.retry_after} секунд")
        rate_limiter.rate_limiter.record_error(chat_id)
        return False
    except TelegramBadRequest as e:
        logging.warning(f"Telegram помилка: {e}")
        rate_limiter.rate_limiter.record_error(chat_id)
        return False
    except Exception as e:
        logging.error(f"Несподівана помилка при відправці: {e}")
        rate_limiter.rate_limiter.record_error(chat_id)
        return False

async def safe_send_message(chat_id: int, text: str) -> bool:
    """Безпечна відправка повідомлення з rate limiting"""
    # Перевірка rate limiting
    if not rate_limiter.rate_limiter.can_send_message(
        chat_id, 
        PERSONA["rate_limit_per_chat"], 
        PERSONA["global_rate_limit"]
    ):
        logging.warning(f"Rate limit: пропускаємо відправку в чат {chat_id}")
        return False
    
    try:
        await bot.send_message(chat_id, text)
        return True
    except TelegramRetryAfter as e:
        logging.warning(f"Telegram rate limit: затримка {e.retry_after} секунд")
        rate_limiter.rate_limiter.record_error(chat_id)
        return False
    except TelegramBadRequest as e:
        logging.warning(f"Telegram помилка: {e}")
        rate_limiter.rate_limiter.record_error(chat_id)
        return False
    except Exception as e:
        logging.error(f"Несподівана помилка при відправці: {e}")
        rate_limiter.rate_limiter.record_error(chat_id)
        return False

# Обробка старту
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(f"Вітаю! Я {PERSONA['name']}. {PERSONA['description']}")

# Єдиний хендлер для всіх повідомлень
@dp.message()
async def universal_handler(message: Message):
    try:
        # Перевіряємо чи повідомлення занадто старе
        if is_message_too_old(message):
            return
        
        # Адмін-команди (пріоритет)
        if message.from_user.id == PERSONA["admin_id"]:
            if message.text and message.text.startswith("/import_history"):
                parts = message.text.split()
                if len(parts) < 3:
                    await safe_reply(message, "Вкажіть шлях до JSON та chat_id: /import_history <шлях_до_json> <chat_id>")
                    return
                json_path = parts[1]
                chat_id = int(parts[2])
                try:
                    result = chat_scanner.import_telegram_history(json_path, chat_id)
                    await safe_reply(message, f"✅ Історію імпортовано! {result} повідомлень додано.")
                except Exception as e:
                    await safe_reply(message, f"❌ Помилка імпорту: {e}")
                return
            elif message.text and message.text.startswith("/"):
                await management.handle(message)
                return
        
        # Групові чати
        if message.chat.type in ["group", "supergroup"]:
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # Відстежуємо активність користувача для анти-спам системи
            smart_behavior.track_user_activity(chat_id, user_id)
            
            # Перевіряємо чи виявлено спам
            if smart_behavior.is_spam_detected(chat_id, user_id):
                # Іноді відповідаємо на спам
                if random.random() < 0.3:  # 30% шанс відповісти
                    spam_reply = smart_behavior.get_spam_reply()
                    await safe_reply(message, spam_reply)
                return
            
            # Автоматичне сканування історії при першому запуску
            if not chat_scanner.is_chat_scanned(chat_id):
                await chat_scanner.auto_scan_chat_history(bot, chat_id)
            
            # Завжди зберігаємо контекст
            context.save_message(message)
            
            # Можливо ставимо реакцію (перед іншими відповідями)
            reaction_posted = await reactions.maybe_react_to_message(message)
            
            # НОВИЙ РОЗУМНИЙ АНАЛІЗ КОНТЕКСТУ
            if message.text:
                # Аналізуємо контекст повідомлення
                recent_messages = [m.get('text', '') for m in context.get_context(chat_id)[-10:]]
                analysis = enhanced_behavior.analyze_conversation_context(message.text, recent_messages)
                
                # Оновлюємо історію аналізу
                enhanced_behavior.update_chat_analysis(chat_id, analysis)
                
                # Логування для розуміння роботи системи
                logging.info(f"Аналіз повідомлення - Тип: {analysis['type']}, Настрій: {analysis['mood']}, Залученість: {analysis['engagement']}")
                
                # Якщо аналіз рекомендує відповісти
                if analysis['should_respond']:
                    # Створюємо контекстно-свідомий промт
                    context_prompt = enhanced_behavior.create_context_aware_prompt(message.text, analysis)
                    
                    # Створюємо фейкове повідомлення з покращеним промтом
                    class EnhancedFakeMessage:
                        def __init__(self, original_message, enhanced_prompt):
                            self.text = enhanced_prompt
                            self.from_user = original_message.from_user
                            self.chat = original_message.chat
                            self.original_text = original_message.text
                    
                    enhanced_msg = EnhancedFakeMessage(message, context_prompt)
                    reply = await gemini.process_message(enhanced_msg)
                    await safe_reply(message, reply)
                    smart_behavior.mark_bot_activity(chat_id)
                    return
            
            # Спонтанна активність з урахуванням трендів
            if enhanced_behavior.should_intervene_spontaneously(chat_id):
                spontaneous_prompt = enhanced_behavior.get_spontaneous_prompt_based_on_trends(chat_id)
                
                class FakeMessage:
                    def __init__(self, text: str):
                        self.text = text
                        self.from_user = type('User', (), {'full_name': PERSONA['name']})
                        self.chat = type('Chat', (), {'id': chat_id})
                
                fake_msg = FakeMessage(spontaneous_prompt)
                reply = await gemini.process_message(fake_msg)
                await safe_reply(message, f"💭 {reply}")
                enhanced_behavior.mark_intervention(chat_id)
                smart_behavior.mark_bot_activity(chat_id, is_spontaneous=True)
                return
    
    except Exception as e:
        chat_id = getattr(message.chat, 'id', 0) if hasattr(message, 'chat') else 0
        logging.error(f"Помилка в universal_handler: {e}")
        
        # Записуємо помилку для rate limiting
        if chat_id:
            rate_limiter.rate_limiter.record_error(chat_id)
        
        # Відповідаємо на помилку тільки якщо не багато помилок і є шанс
        if (chat_id and 
            not rate_limiter.rate_limiter.should_suppress_errors(chat_id) and 
            random.random() < PERSONA["error_reply_chance"]):
            await safe_reply(message, "Ой, щось пішло не так... 🤖")

async def spontaneous_activity_loop():
    """Покращена фонова задача для спонтанної активності з аналізом трендів"""
    while True:
        try:
            await asyncio.sleep(300)  # Перевіряємо кожні 5 хвилин
            
            # Отримуємо список активних чатів
            from bot.modules.context import get_active_chats
            active_chats = get_active_chats()
            
            for chat_id in active_chats:
                # Використовуємо покращену логіку втручання
                if enhanced_behavior.should_intervene_spontaneously(chat_id):
                    # Генеруємо промт на основі трендів чату
                    spontaneous_prompt = enhanced_behavior.get_spontaneous_prompt_based_on_trends(chat_id)
                    
                    class FakeMessage:
                        def __init__(self, text: str):
                            self.text = text
                            self.from_user = type('User', (), {'full_name': PERSONA['name']})
                            self.chat = type('Chat', (), {'id': chat_id})
                    
                    fake_msg = FakeMessage(spontaneous_prompt)
                    reply = await gemini.process_message(fake_msg)
                    
                    # Відправляємо повідомлення в чат
                    await safe_send_message(chat_id, f"💭 {reply}")
                    enhanced_behavior.mark_intervention(chat_id)
                    smart_behavior.mark_bot_activity(chat_id, is_spontaneous=True)
                    
                    # Логуємо активність
                    trends = enhanced_behavior.get_chat_trends(chat_id)
                    logging.info(f"Спонтанна активність в чаті {chat_id}: активність={trends['activity']}, настрій={trends['mood_trend']}")
                    
                    # Затримка між спонтанними повідомленнями в різних чатах
                    await asyncio.sleep(30)
                    
                    # Затримка між спонтанними повідомленнями в різних чатах
                    await asyncio.sleep(30)
                    
        except Exception as e:
            logging.error(f"Помилка в spontaneous_activity_loop: {e}")
            await asyncio.sleep(60)  # Більша затримка при помилці

async def main():
    # Запускаємо фонову задачу для спонтанної активності
    asyncio.create_task(spontaneous_activity_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
