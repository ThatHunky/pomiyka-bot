# Мапа для стислих описів медіа (стікери, фото, аудіо)
import json
import os
from typing import Literal
from bot.bot_config import MEDIA_MAP_PATH

def load_media_map():
    if os.path.exists(MEDIA_MAP_PATH):
        with open(MEDIA_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_media_map(media_map):
    # Створюємо директорію якщо не існує
    os.makedirs(os.path.dirname(MEDIA_MAP_PATH), exist_ok=True)
    with open(MEDIA_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(media_map, f, ensure_ascii=False, indent=2)

def get_or_add_media(media_id: str, media_type: Literal["sticker","photo","audio","voice","video"], summary: str):
    media_map = load_media_map()
    if media_id in media_map:
        return media_map[media_id]
    
    # Простий абсурдний підпис замість Gemini (швидше)
    absurd_prefixes = {
        "sticker": "🎭 Магічний артефакт:",
        "photo": "📸 Спіймана реальність:",
        "audio": "🎵 Звукова хвиля з майбутнього:",
        "voice": "🎤 Голос з паралельного всесвіту:",
        "video": "🎬 Кінострічка реальності:"
    }
    
    desc = f"{absurd_prefixes.get(media_type, '🤖')} {summary}"
    media_map[media_id] = f"[{media_type.upper()}:{media_id[:8]}] {desc}"
    save_media_map(media_map)
    return media_map[media_id]
