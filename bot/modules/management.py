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
    
    elif message.text == "/rescan":
        try:
            from bot.modules.chat_scanner import reset_chat_scan_state, auto_scan_chat_history
            from aiogram import Bot
            from bot.bot_config import PERSONA
            
            chat_id = message.chat.id
            
            # Перевіряємо, чи це груповий чат
            if message.chat.type not in ["group", "supergroup"]:
                await message.reply("❌ Команда /rescan доступна лише в групових чатах.")
                return
            
            # Скидаємо стан сканування
            reset_chat_scan_state(chat_id)
            
            # Отримуємо бота з глобального контексту main.py
            import sys
            if hasattr(sys.modules.get('bot.main'), 'bot'):
                bot = sys.modules['bot.main'].bot
                
                await message.reply("🔄 Починаю повторне сканування історії чату...")
                
                # Запускаємо сканування асинхронно
                import asyncio
                asyncio.create_task(auto_scan_chat_history(bot, chat_id))
                
                await message.reply("✅ Сканування запущено! Історія чату буде оновлена.")
            else:
                await message.reply("❌ Не вдалося отримати доступ до бота для сканування.")
            
            return
        except Exception as e:
            await message.reply(f"❌ Помилка при повторному скануванні: {e}")
            return
    
    elif message.text == "/reactions":
        try:
            from bot.modules.reactions import get_all_available_reactions
            reactions_list = get_all_available_reactions()
            reactions_text = "🎭 Доступні реакції бота:\n" + " ".join(reactions_list[:20])  # Показуємо перші 20
            if len(reactions_list) > 20:
                reactions_text += f"\n... та ще {len(reactions_list) - 20} інших!"
            await message.reply(reactions_text)
            return
        except Exception as e:
            await message.reply(f"❌ Помилка отримання реакцій: {e}")
            return
    
    # Всі інші команди через абсурдного Гряга
    if message.text == "/stats":
        prompt = (
            "Ти — Гряг, абсурдний бот-дух. Відповідай на адмінські команди у стилі абсурду, мемів, парадоксів. "
            "Ось команда: /stats. Відповідь має бути короткою, дотепною, але інформативною про стан бота."
        )
    elif message.text == "/help":
        prompt = (
            "Ти — Гряг, дружелюбний бот з легким гумором. Покажи список доступних адмін-команд у веселому, але зрозумілому стилі. "
            "Команди: /stats, /help, /clear_context, /rescan, /reactions, /import_history"
        )
    else:
        prompt = (
            "Ти — Гряг, дружелюбний бот з легким гумором. Відповідай на адмінські команди у веселому, дружньому стилі. "
            f"Ось команда: {message.text}. Якщо не знаєш — запропонуй /help"
        )
    
    fake_msg = FakeMessage(prompt)
    reply = await process_message(fake_msg)
    await message.reply(reply)
