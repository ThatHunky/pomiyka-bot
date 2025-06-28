# Утилітарні функції для бота Гряг
from typing import Optional, Dict, List, Any

class FakeMessage:
    """Фейковий об'єкт Message для спонтанних/системних відповідей."""
    def __init__(self, text: str, chat_id: int, user_name: Optional[str] = None, 
                 processed_context: Optional[List[Dict[str, Any]]] = None,
                 recommendations: Optional[Dict[str, Any]] = None):
        self.text = text
        self.from_user = type('User', (), {'full_name': user_name or 'Гряг'})
        self.chat = type('Chat', (), {'id': chat_id})
        self.processed_context = processed_context
        self.recommendations = recommendations
