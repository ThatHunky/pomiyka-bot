# Основний файл запуску Telegram-бота
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
import asyncio
import logging
from bot.modules import context, gemini, management, media_map, random_life, smart_behavior, chat_scanner, reactions
from bot.bot_config import PERSONA
import os
from dotenv import load_dotenv
import random
from datetime import datetime, timezone, timedelta

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
                    await message.reply("Вкажіть шлях до JSON та chat_id: /import_history <шлях_до_json> <chat_id>")
                    return
                json_path = parts[1]
                chat_id = int(parts[2])
                try:
                    result = chat_scanner.import_telegram_history(json_path, chat_id)
                    await message.reply(f"✅ Історію імпортовано! {result} повідомлень додано.")
                except Exception as e:
                    await message.reply(f"❌ Помилка імпорту: {e}")
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
                    await message.reply(spam_reply)
                return
            
            # Автоматичне сканування історії при першому запуску
            if not chat_scanner.is_chat_scanned(chat_id):
                await chat_scanner.auto_scan_chat_history(bot, chat_id)
            
            # Завжди зберігаємо контекст
            context.save_message(message)
            
            # Можливо ставимо реакцію (перед іншими відповідями)
            reaction_posted = await reactions.maybe_react_to_message(message)
            
            # Перевіряємо чи потрібна спонтанна активність (раз на N хвилин)
            if smart_behavior.should_be_spontaneous(chat_id):
                recent_context = [m.get('text', '') for m in context.get_context(chat_id)[-5:]]
                prompt = smart_behavior.get_spontaneous_prompt(recent_context)
                
                class FakeMessage:
                    def __init__(self, text: str):
                        self.text = text
                        self.from_user = type('User', (), {'full_name': PERSONA['name']})
                        self.chat = type('Chat', (), {'id': 0})
                
                fake_msg = FakeMessage(prompt)
                reply = await gemini.process_message(fake_msg)
                await message.reply(f"💭 {reply}")
                smart_behavior.mark_bot_activity(chat_id, is_spontaneous=True)
                return
            
            # Рандомна відповідь на тригери (згадки імені)
            if message.text and random_life.should_reply_randomly(message.text):
                if random.random() < PERSONA["random_reply_chance"]:
                    recent_context = [m.get('text', '') for m in context.get_context(chat_id)[-5:]]
                    reply = await random_life.get_random_reply(recent_context)
                    await message.reply(reply)
                    smart_behavior.mark_bot_activity(chat_id)
                    return
            
            # Розумна відповідь на звичайні повідомлення (рідко)
            if smart_behavior.should_reply_smart(chat_id, message.text or ""):
                reply = await gemini.process_message(message)
                await message.reply(reply)
                smart_behavior.mark_bot_activity(chat_id)
    
    except Exception as e:
        logging.error(f"Помилка в universal_handler: {e}")
        await message.reply("Ой, щось пішло не так... 🤖")

async def spontaneous_activity_loop():
    """Фонова задача для спонтанної активності"""
    while True:
        try:
            await asyncio.sleep(300)  # Перевіряємо кожні 5 хвилин
            
            # Отримуємо список активних чатів
            from bot.modules.context import get_active_chats
            active_chats = get_active_chats()
            
            for chat_id in active_chats:
                # Перевіряємо чи потрібна спонтанна активність
                if smart_behavior.should_be_spontaneous(chat_id):
                    recent_context = [m.get('text', '') for m in context.get_context(chat_id)[-5:]]
                    prompt = smart_behavior.get_spontaneous_prompt(recent_context)
                    
                    class FakeMessage:
                        def __init__(self, text: str):
                            self.text = text
                            self.from_user = type('User', (), {'full_name': PERSONA['name']})
                            self.chat = type('Chat', (), {'id': chat_id})
                    
                    fake_msg = FakeMessage(prompt)
                    reply = await gemini.process_message(fake_msg)
                    
                    # Відправляємо повідомлення в чат
                    await bot.send_message(chat_id, f"💭 {reply}")
                    smart_behavior.mark_bot_activity(chat_id, is_spontaneous=True)
                    
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
