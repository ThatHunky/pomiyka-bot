# Мапа для стислих описів медіа (стікери, фото, аудіо)
MEDIA_MAP_FILE = "bot/media_map.json"

import json
import os
from typing import Literal

def load_media_map():
    if os.path.exists(MEDIA_MAP_FILE):
        with open(MEDIA_MAP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_media_map(media_map):
    with open(MEDIA_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(media_map, f, ensure_ascii=False, indent=2)

def get_or_add_media(media_id: str, media_type: Literal["sticker","photo","audio"], summary: str):
    # Додаємо абсурдний підпис через Gemini (асинхронно, якщо можливо)
    try:
        from bot.modules.gemini import process_message
        class FakeMessage:
            def __init__(self, text: str):
                self.text = text
                self.from_user = type('User', (), {'full_name': 'Глек'})
                self.chat = type('Chat', (), {'id': 0})
        prompt = f"Ти — Глек, абсурдний бот. Придумай короткий, абсурдний, україномовний підпис для {media_type} з описом '{summary}'."
        fake_msg = FakeMessage(prompt)
        import asyncio
        loop = asyncio.get_event_loop()
        desc = loop.run_until_complete(process_message(fake_msg))
    except Exception:
        desc = summary
    media_map = load_media_map()
    if media_id in media_map:
        return media_map[media_id]
    media_map[media_id] = f"[{media_type.upper()}:{media_id}] {desc}"
    save_media_map(media_map)
    return media_map[media_id]
