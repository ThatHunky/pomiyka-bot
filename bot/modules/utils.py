# Утилітарні функції для бота Гряг
from typing import Optional

class FakeMessage:
    """Фейковий об'єкт Message для спонтанних/системних відповідей."""
    def __init__(self, text: str, chat_id: int, user_name: Optional[str] = None):
        self.text = text
        self.from_user = type('User', (), {'full_name': user_name or 'Гряг'})
        self.chat = type('Chat', (), {'id': chat_id})
