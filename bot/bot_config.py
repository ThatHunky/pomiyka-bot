import os
from dotenv import load_dotenv

load_dotenv()

# Конфіг для особистості бота та лімітів
PERSONA = {
    "name": os.getenv("BOT_PERSONA_NAME", "Помийка"),
    "description": os.getenv("BOT_PERSONA_DESC", "Я україномовний бот-помічник для групових чатів, завжди готовий допомогти!"),
    "context_limit": int(os.getenv("BOT_CONTEXT_LIMIT", 20)),
    "reply_timeout": int(os.getenv("BOT_REPLY_TIMEOUT", 10)),
    "admin_id": int(os.getenv("ADMIN_ID", 392817811))
}
