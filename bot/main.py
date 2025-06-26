# Основний файл запуску Telegram-бота
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
import asyncio
import logging
from bot.modules import context, gemini, management, media_map, context_sqlite, random_life
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
                    context_sqlite.import_telegram_history(json_path, chat_id)
                    await message.reply("Історію імпортовано!")
                except Exception as e:
                    await message.reply(f"Помилка імпорту: {e}")
                return
            elif message.text and message.text.startswith("/"):
                await management.handle(message)
                return
        
        # Групові чати
        if message.chat.type in ["group", "supergroup"]:
            # Зберігаємо контекст
            context.save_message(message)
            
            # Рандомна відповідь, якщо згадано бота
            if message.text and random_life.should_reply_randomly(message.text):
                if random.random() < 0.5:  # 50% ймовірність відповісти
                    recent_context = [m['text'] for m in context.get_context(message.chat.id)[-5:]]
                    reply = await random_life.get_random_reply(recent_context)
                    await message.reply(reply)
                    return
            
            # Звичайна відповідь через Gemini
            reply = await gemini.process_message(message)
            await message.reply(reply)
    
    except Exception as e:
        logging.error(f"Помилка в universal_handler: {e}")
        await message.reply("Ой, щось пішло не так... 🤖")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
