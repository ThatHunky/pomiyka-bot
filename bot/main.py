# Основний файл запуску Telegram-бота
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
import asyncio
import logging
from bot.modules import context, gemini, management, media_map, random_life, smart_behavior, chat_scanner
from bot.bot_config import PERSONA
import os
from dotenv import load_dotenv
import random

load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обробка старту
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(f"Вітаю! Я {PERSONA['name']}. {PERSONA['description']}")

# Єдиний хендлер для всіх повідомлень
@dp.message()
async def universal_handler(message: Message):
    try:
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
            
            # Автоматичне сканування історії при першому запуску
            if not chat_scanner.is_chat_scanned(chat_id):
                await chat_scanner.auto_scan_chat_history(bot, chat_id)
            
            # Завжди зберігаємо контекст
            context.save_message(message)
            
            # Перевіряємо чи потрібна спонтанна активність (раз на N хвилин)
            if smart_behavior.should_be_spontaneous(chat_id):
                recent_context = [m['text'] for m in context.get_context(chat_id)[-5:]]
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
                    recent_context = [m['text'] for m in context.get_context(chat_id)[-5:]]
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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
