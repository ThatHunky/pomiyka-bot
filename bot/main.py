# Основний файл запуску Telegram-бота з покращеннями
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

# Імпорт нових модулів покращень
from bot.modules.config_validator import validate_startup_config, quick_validate
from bot.modules.performance_monitor import (
    performance_monitor, start_monitoring_task, 
    record_api_call, record_message_processed, get_health_status
)
from bot.modules.security_manager import SecurityManager, validate_message_security, check_rate_limit

# Імпорт функцій очищення для memory management  
from bot.modules.local_analyzer import get_analyzer
from bot.modules.enhanced_behavior import cleanup_old_analysis_data

# Перевірка конфігурації при старті
load_dotenv()

# Швидка валідація критичних параметрів
if not quick_validate():
    raise ValueError("Критичні змінні середовища відсутні")

# Повна валідація конфігурації
if not validate_startup_config():
    logging.warning("Конфігурація містить попередження, але бот може працювати")

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not API_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не знайдено в змінних середовища")

logging.basicConfig(level=logging.INFO)

# Глобальний бот для доступу з інших модулів (наприклад, /rescan)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Ініціалізація Security Manager
security_manager = SecurityManager()

def validate_config() -> None:
    """Перевіряє наявність критичних змінних середовища."""
    required_vars = ["TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Відсутні обов'язкові змінні: {', '.join(missing)}")

validate_config()

def is_message_too_old(message: Message) -> bool:
    """Перевіряє чи повідомлення занадто старе для обробки"""
    if not PERSONA["ignore_old_messages"]:
        return False
    if not message.date:
        return False
    
    now = datetime.now(timezone.utc)
    message_time = message.date
    
    # Конвертуємо message_time у UTC якщо потрібно
    if message_time.tzinfo is None:
        message_time = message_time.replace(tzinfo=timezone.utc)
    
    age_minutes = (now - message_time).total_seconds() / 60
    max_age = PERSONA["max_message_age_minutes"]
    
    if age_minutes > max_age:
        logging.info(f"Ігноруємо старе повідомлення (вік: {age_minutes:.1f} хв, максимум: {max_age} хв)")
        return True
    
    return False

async def safe_reply(message: Message, text: str, chat_id: Optional[int] = None) -> bool:
    """Безпечна відправка відповіді з rate limiting та error handling"""
    if chat_id is None:
        chat_id = message.chat.id
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
async def start_handler(message: Message) -> None:
    """Вітальний хендлер"""
    await message.answer(f"Вітаю! Я {PERSONA['name']}. {PERSONA['description']}")

# Єдиний хендлер для всіх повідомлень
@dp.message()
async def universal_handler(message: Message) -> None:
    """Універсальний хендлер для всіх повідомлень"""
    try:
        # Перевіряємо чи повідомлення занадто старе
        if is_message_too_old(message):
            logging.info(f"Повідомлення проігноровано через вік: {message.date}")
            return
        
        # Перевірка None для from_user
        if not message.from_user or not getattr(message.from_user, 'id', None):
            logging.warning("message.from_user відсутній, ігноруємо повідомлення")
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
            
            # ===== БЕЗПЕКА ТА ВАЛІДАЦІЯ =====
            # Перевіряємо безпеку повідомлення
            if message.text:
                is_safe, security_reason = security_manager.validate_message(message.text, user_id)
                if not is_safe:
                    logging.warning(f"Небезпечне повідомлення від {user_id}: {security_reason}")
                    return
            
            # Перевіряємо rate limiting
            if not security_manager.rate_limit_check(user_id):
                logging.info(f"Rate limit exceeded for user {user_id}")
                return
            
            # Відстежуємо активність користувача для анти-спам системи
            smart_behavior.track_user_activity(chat_id, user_id)
            
            # Перевіряємо чи виявлено спам
            if smart_behavior.is_spam_detected(chat_id, user_id):
                # Іноді відповідаємо на спам
                if random.random() < PERSONA["spam_reply_chance"]:
                    spam_reply = smart_behavior.get_spam_reply()
                    await safe_reply(message, spam_reply)
                return
            
            # Автоматичне сканування історії при першому запуску
            if not chat_scanner.is_chat_scanned(chat_id):
                await chat_scanner.auto_scan_chat_history(bot, chat_id)
            
            # Завжди зберігаємо контекст
            from bot.modules.context_sqlite import save_message
            await save_message(message)
            
            # Можливо ставимо реакцію (перед іншими відповідями)
            reaction_posted = await reactions.maybe_react_to_message(message)
            
            # СПРОЩЕНА ЛОГІКА З ПОКРАЩЕНИМ КОНТЕКСТОМ
            if message.text:
                # Отримуємо контекст чату з іменами користувачів
                from bot.modules.context_sqlite import get_context
                chat_context = await get_context(chat_id)
                user_name = getattr(message.from_user, 'full_name', 'Невідомий')
                
                # Використовуємо покращену логіку з enhanced_behavior
                analysis = enhanced_behavior.generate_enhanced_response(message, chat_context)
                
                # Логування для розуміння роботи системи
                logging.info(f"Аналіз - Чат: {chat_id}, Користувач: {user_name}, "
                           f"Тип: {analysis.get('conversation_type', 'невідомий')}, "
                           f"Настрій: {analysis.get('mood', 'нейтральний')}, "
                           f"Рівень залученості: {analysis.get('engagement_level', 0)}, "
                           f"Відповідь: {analysis.get('should_reply', False)}")
                
                # Перевіряємо чи потрібно відповідати
                if analysis.get('should_reply', False):
                    # Отримуємо інструкцію для тону
                    tone_instruction = analysis.get('tone_instruction', '')
                    
                    # Створюємо покращене повідомлення з контекстом
                    enhanced_message = FakeMessage(
                        text=message.text,
                        chat_id=chat_id,
                        user_name=user_name,
                        processed_context=str(chat_context[-10:]),  # Останні 10 повідомлень
                        recommendations=analysis
                    )
                    
                    # Генеруємо відповідь через Gemini
                    reply = await gemini.process_message(enhanced_message, tone_instruction)
                    
                    # Обрізаємо відповідь якщо потрібно
                    max_length = analysis.get('max_response_length', 200)
                    if len(reply) > max_length:
                        reply = reply[:max_length-3] + "..."
                    
                    await safe_reply(message, reply)
                    smart_behavior.mark_bot_activity(chat_id)
                    return
            
            # Спонтанна активність з урахуванням трендів
            if enhanced_behavior.should_intervene_spontaneously(chat_id):
                spontaneous_prompt = enhanced_behavior.get_spontaneous_prompt_based_on_trends(chat_id)
                
                fake_msg = FakeMessage(spontaneous_prompt, chat_id, PERSONA['name'])
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

async def memory_cleanup_task() -> None:
    """Фонова задача для очищення пам'яті та застарілих даних"""
    while True:
        try:
            await asyncio.sleep(3600)  # Виконуємо кожну годину
            
            logging.info("Запуск задачі очищення пам'яті...")
            
            # Очищення старих даних аналізу (7 днів)
            try:
                await cleanup_old_analysis_data(days=7)
                logging.info("Очищення enhanced_behavior даних завершено")
            except Exception as e:
                logging.error(f"Помилка очищення enhanced_behavior: {e}")
            
            # Очищення кешу локального аналізатора
            try:
                analyzer = get_analyzer()
                if hasattr(analyzer, 'cleanup_old_data'):
                    analyzer.cleanup_old_data(days=7)
                    logging.info("Очищення local_analyzer кешу завершено")
            except Exception as e:
                logging.error(f"Помилка очищення local_analyzer: {e}")
                
            # Експорт метрик продуктивності
            try:
                performance_monitor.export_metrics()
                logging.info("Експорт метрик продуктивності завершено")
            except Exception as e:
                logging.error(f"Помилка експорту метрик: {e}")
                
            logging.info("Задача очищення пам'яті завершена успішно")
                
        except Exception as e:
            logging.error(f"Критична помилка в memory_cleanup_task: {e}")
            await asyncio.sleep(300)  # Затримка при помилці

async def database_initialization_task() -> None:
    """Ініціалізація всіх асинхронних баз даних при старті"""
    try:
        logging.info("Ініціалізація асинхронних баз даних...")
        
        # Ініціалізуємо context database
        from bot.modules.context_sqlite import init_db
        await init_db()
        
        # Ініціалізуємо local analyzer database
        analyzer = get_analyzer()
        if hasattr(analyzer, '_ensure_db_initialized'):
            await analyzer._ensure_db_initialized()
        
        logging.info("Ініціалізація асинхронних баз даних завершена")
        
    except Exception as e:
        logging.error(f"Помилка ініціалізації баз даних: {e}")
        raise

async def spontaneous_activity_loop() -> None:
    while True:
        try:
            await asyncio.sleep(300)  # Перевіряємо кожні 5 хвилин
            
            # Отримуємо список активних чатів
            from bot.modules.context_sqlite import get_active_chats
            active_chats = await get_active_chats()
            
            for chat_id in active_chats:
                # Використовуємо покращену логіку втручання
                if enhanced_behavior.should_intervene_spontaneously(chat_id):
                    # Генеруємо промт на основі трендів чату
                    spontaneous_prompt = enhanced_behavior.get_spontaneous_prompt_based_on_trends(chat_id)
                    
                    fake_msg = FakeMessage(spontaneous_prompt, chat_id, PERSONA['name'])
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
                    
        except Exception as e:
            logging.error(f"Помилка в spontaneous_activity_loop: {e}")
            await asyncio.sleep(60)  # Більша затримка при помилці

async def shutdown(dispatcher: Dispatcher) -> None:
    """Graceful shutdown для бота"""
    logging.info("Завершення роботи бота...")
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

async def main() -> None:
    """Головна точка входу"""
    
    # Ініціалізація асинхронних баз даних при старті
    await database_initialization_task()
    
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(dp)))
    
    # Запускаємо фонові задачі
    asyncio.create_task(spontaneous_activity_loop())
    asyncio.create_task(memory_cleanup_task())
    asyncio.create_task(start_monitoring_task())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

class FakeMessage:
    """Фейкове повідомлення для сумісності з API"""
    def __init__(self, text: str, chat_id: int = 0, user_name: str = "System", 
                 processed_context: Optional[str] = None, recommendations: Optional[Dict[str, Any]] = None):
        self.text = text
        self.processed_context = processed_context
        self.recommendations = recommendations or {}
        
        # Створюємо фейкові об'єкти для сумісності
        self.chat = type('Chat', (), {'id': chat_id})()
        self.from_user = type('User', (), {
            'full_name': user_name,
            'id': 0,
            'username': user_name.lower().replace(' ', '_')
        })()
