# Модуль для збереження та отримання контексту чату (тільки SQLite)
from aiogram.types import Message
from .media_map import get_or_add_media
from bot.modules.context_sqlite import save_message as save_message_sqlite, get_context as get_context_sqlite

def save_message(message: Message):
    # Визначаємо медіа для SQLite
    media_id = None
    media_type = None
    text_for_context = message.text
    
    if message.sticker:
        media_id = message.sticker.file_unique_id
        media_type = "sticker"
        text_for_context = get_or_add_media(media_id, "sticker", f"Стікер: {message.sticker.emoji or ''}")
    elif message.photo:
        media_id = message.photo[-1].file_unique_id
        media_type = "photo"
        text_for_context = get_or_add_media(media_id, "photo", "Фото")
    elif message.audio:
        media_id = message.audio.file_unique_id
        media_type = "audio"
        text_for_context = get_or_add_media(media_id, "audio", f"Аудіо: {message.audio.title or ''}")
    elif message.voice:
        media_id = message.voice.file_unique_id
        media_type = "voice"
        text_for_context = get_or_add_media(media_id, "voice", "Голосове")
    elif message.video:
        media_id = message.video.file_unique_id
        media_type = "video"
        text_for_context = get_or_add_media(media_id, "video", "Відео")
    elif not text_for_context:
        text_for_context = "[Непідтримуваний тип повідомлення]"
    
    # Створюємо фейковий Message для SQLite
    class SQLiteMessage:
        def __init__(self, original_msg, text_override):
            self.chat = original_msg.chat
            self.from_user = original_msg.from_user
            self.text = text_override
    
    sqlite_msg = SQLiteMessage(message, text_for_context)
    save_message_sqlite(sqlite_msg, media_id, media_type)

def get_context(chat_id):
    from bot.bot_config import PERSONA
    # Отримуємо контекст з SQLite
    context_list = get_context_sqlite(chat_id, limit=PERSONA["context_limit"]*10)
    
    # Додаємо mood analysis та summary
    if context_list:
        moods = []
        for m in context_list[-10:]:
            text = m.get("text", "").lower()
            if any(word in text for word in ["жарт", "ахах", "лол", "😂", "хаха"]):
                moods.append("жарт")
            elif any(word in text for word in ["свар", "лайк", "гнів", "злість"]):
                moods.append("сварка")
            elif len(text.strip()) < 2:
                moods.append("тиша")
            else:
                moods.append("звичайний")
        
        from collections import Counter
        mood_summary = Counter(moods).most_common(1)[0][0] if moods else "звичайний"
        context_list.insert(0, {"user": "Гряг", "text": f"Обстановка в чаті: {mood_summary}"})
    
    return context_list

def get_active_chats():
    """Повертає список активних чатів"""
    from bot.modules.context_sqlite import get_active_chats as get_active_chats_sqlite
    return get_active_chats_sqlite()
