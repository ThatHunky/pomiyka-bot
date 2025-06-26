# Модуль для менеджменту (доступно лише адміністратору)
from aiogram.types import Message

async def handle(message: Message):
    from bot.modules.gemini import process_message
    class FakeMessage:
        def __init__(self, text: str):
            self.text = text
            self.from_user = type('User', (), {'full_name': 'Гряг'})
            self.chat = type('Chat', (), {'id': 0})
    
    # Спеціальні команди без Gemini
    if message.text == "/clear_context":
        try:
            from bot.bot_config import DB_PATH
            import os
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
                await message.reply("🧹 Контекст очищено! Пам'ять стерта.")
            else:
                await message.reply("🤔 База даних не знайдена, нічого очищати.")
            return
        except Exception as e:
            await message.reply(f"❌ Помилка очищення: {e}")
            return
    
    elif message.text == "/stats":
        try:
            from bot.modules.context_sqlite import get_global_stats
            from bot.bot_config import DB_PATH
            import os
            
            if not os.path.exists(DB_PATH):
                stats_text = "📊 Статистика:\n• База даних: не створена\n• Повідомлень: 0\n• Чатів: 0"
            else:
                stats = get_global_stats()
                stats_text = f"📊 Статистика:\n• Повідомлень у базі: {stats['total_messages']}\n• Активних чатів: {stats['active_chats']}\n• База: {DB_PATH}"
            
            await message.reply(stats_text)
            return
        except Exception as e:
            await message.reply(f"❌ Помилка отримання статистики: {e}")
            return
    
    # Всі інші команди через абсурдного Гряга
    if message.text == "/stats":
        prompt = (
            "Ти — Гряг, абсурдний бот-дух. Відповідай на адмінські команди у стилі абсурду, мемів, парадоксів. "
            "Ось команда: /stats. Відповідь має бути короткою, дотепною, але інформативною про стан бота."
        )
    elif message.text == "/help":
        prompt = (
            "Ти — Гряг, абсурдний бот-дух. Покажи список доступних адмін-команд у абсурдному стилі. "
            "Команди: /stats, /help, /clear_context, /import_history"
        )
    else:
        prompt = (
            "Ти — Гряг, абсурдний бот-дух. Відповідай на адмінські команди у стилі абсурду, мемів, парадоксів. "
            f"Ось команда: {message.text}. Якщо не знаєш — запропонуй /help"
        )
    
    fake_msg = FakeMessage(prompt)
    reply = await process_message(fake_msg)
    await message.reply(reply)
