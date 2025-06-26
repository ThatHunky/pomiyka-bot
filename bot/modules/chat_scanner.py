# Модуль для автоматичного сканування історії чату
import json
import os
from aiogram import Bot
from aiogram.types import Message, Chat
from datetime import datetime
from bot.bot_config import CHAT_STATE_PATH, PERSONA, DB_PATH
from bot.modules.context_sqlite import save_message_obj
import asyncio
import logging

# Стан сканованих чатів
def load_chat_states():
    if os.path.exists(CHAT_STATE_PATH):
        with open(CHAT_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_chat_states(states):
    os.makedirs(os.path.dirname(CHAT_STATE_PATH), exist_ok=True)
    with open(CHAT_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(states, f, ensure_ascii=False, indent=2)

def mark_chat_scanned(chat_id: int):
    states = load_chat_states()
    states[str(chat_id)] = {
        "scanned": True,
        "scan_date": datetime.now().isoformat(),
        "last_message_id": None
    }
    save_chat_states(states)

def is_chat_scanned(chat_id: int) -> bool:
    states = load_chat_states()
    return states.get(str(chat_id), {}).get("scanned", False)

def reset_chat_scan_state(chat_id: int):
    """Скидає стан сканування чату для повторного сканування"""
    states = load_chat_states()
    if str(chat_id) in states:
        del states[str(chat_id)]
        save_chat_states(states)
        logging.info(f"Скинуто стан сканування для чату {chat_id}")

async def auto_scan_chat_history(bot: Bot, chat_id: int):
    """Автоматично сканує історію чату та додає в базу"""
    if not PERSONA["auto_scan_history"]:
        return
    
    if is_chat_scanned(chat_id):
        logging.info(f"Чат {chat_id} вже сканований, пропускаю...")
        return
    
    try:
        logging.info(f"🔍 Починаю сканування історії чату {chat_id}...")
        
        # Отримуємо інформацію про чат
        chat = await bot.get_chat(chat_id)
        
        # Позначаємо чат як сканований одразу (щоб не повторювати)
        mark_chat_scanned(chat_id)
        
        # Оскільки Telegram API обмежує доступ до історії,
        # просто логуємо що чат готовий до роботи
        logging.info(f"✅ Чат {chat_id} ({chat.title or 'Без назви'}) готовий до роботи")
        logging.info(f"ℹ️ Нові повідомлення будуть автоматично додаватися в контекст")
            
    except Exception as e:
        logging.error(f"❌ Помилка ініціалізації чату {chat_id}: {e}")

async def scan_on_join(bot: Bot, message: Message):
    """Викликається коли бот приєднується до нового чату"""
    if message.chat.type in ["group", "supergroup"]:
        # Запускаємо сканування в фоні
        asyncio.create_task(auto_scan_chat_history(bot, message.chat.id))

def import_telegram_history(json_path: str, chat_id: int):
    """Імпортує історію чату з JSON файлу Telegram Desktop"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        messages_imported = 0
        
        # Парсимо JSON структуру Telegram Desktop
        if "messages" in data:
            for msg in data["messages"]:
                try:
                    # Отримуємо базову інформацію
                    text = ""
                    user = "Unknown"
                    timestamp = datetime.now().isoformat()
                    
                    # Текст повідомлення
                    if isinstance(msg.get("text"), str):
                        text = msg["text"]
                    elif isinstance(msg.get("text"), list):
                        # Складений текст з форматуванням
                        text_parts = []
                        for part in msg["text"]:
                            if isinstance(part, str):
                                text_parts.append(part)
                            elif isinstance(part, dict) and "text" in part:
                                text_parts.append(part["text"])
                        text = "".join(text_parts)
                    
                    # Медіа файли
                    if msg.get("photo"):
                        text += " [фото]"
                    if msg.get("sticker_emoji"):
                        text += f" [стікер: {msg['sticker_emoji']}]"
                    if msg.get("file"):
                        text += " [файл]"
                    if msg.get("voice_message"):
                        text += " [голосове]"
                    
                    # Автор
                    if "from" in msg:
                        user = msg["from"]
                    elif "actor" in msg:
                        user = msg["actor"]
                    
                    # Час
                    if "date" in msg:
                        timestamp = msg["date"]
                    
                    # Зберігаємо в базу
                    if text.strip():
                        save_message_obj(
                            chat_id=chat_id,
                            user=user,
                            text=text.strip(),
                            timestamp=timestamp
                        )
                        messages_imported += 1
                        
                except Exception as msg_error:
                    logging.warning(f"Помилка обробки повідомлення: {msg_error}")
                    continue
        
        logging.info(f"✅ Імпортовано {messages_imported} повідомлень з {json_path}")
        return messages_imported
        
    except Exception as e:
        logging.error(f"❌ Помилка імпорту історії: {e}")
        raise e

def get_chat_context_summary(chat_id: int) -> str:
    """Повертає короткий summary контексту чату"""
    from bot.modules.context_sqlite import get_context
    context = get_context(chat_id, limit=10)
    
    if not context:
        return "Новий чат без історії"
    
    total_messages = len(context)
    recent_users = list(set([m.get("user", "Unknown") for m in context[-5:]]))
    
    return f"Історія: {total_messages} повідомлень, активні: {', '.join(recent_users[:3])}"
