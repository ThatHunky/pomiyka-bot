import os
import random
from bot.modules import gemini
import asyncio
from typing import List, Optional
import inspect

# Слова-тригери для згадки бота
TRIGGERS = [
    os.getenv("BOT_PERSONA_NAME", "гряг").lower(),
    "@gryag_bot", "гряг", "грягік", "грягу", "гряга", "грягом", "бот", "боте"
]

# Можливі рандомні відповіді (дружелюбні)
RANDOM_REPLIES = [
    "Привіт! Що цікавого?",
    "Я тут! Чим можу допомогти?",
    "Мене кликали? Завжди радий поспілкуватися!",
    "О, знову про мене! Це приємно 😊",
    "Можливо, час поговорити про щось цікаве?",
    "Я все бачу і завжди готовий до розмови!",
    "Хтось хоче дружньої бесіди?",
    "Люблю, коли мене згадують! Що нового?"
]

def should_reply_randomly(text: str) -> bool:
    text = text.lower()
    return any(trigger in text for trigger in TRIGGERS)

async def get_random_reply(context_messages: Optional[List[str]] = None) -> str:
    # Динамічна персона на основі контексту  
    persona_base = (
        "Ти — Гряг, дружелюбний україномовний чат-бот з легким гумором. "
        "Ти корисний, розумний та завжди готовий підтримати розмову цікавою репліку. "
        "Твій стиль — це дружелюбність, легкий гумор та позитивне ставлення. "
        "Ти адекватний та приємний у спілкуванні. "
        "Завжди підлаштовуй свою манеру під настрій чату, але залишайся дружелюбним. "
        "Якщо в чаті жартують — додай свій дотепний коментар. Якщо серйозно — будь підтримуючим. "
        "Згенеруй коротку, дотепну, україномовну відповідь на згадку про себе у груповому чаті. Будь приємним та корисним у спілкуванні."
    )
    prompt = persona_base
    if context_messages:
        prompt += " Ось кілька попередніх повідомлень чату: " + " ".join(context_messages)
    # Створюємо фейковий Message для сумісності
    class FakeMessage:
        def __init__(self, text: str):
            self.text = text
            self.from_user = type('User', (), {'full_name': 'Гряг'})
            self.chat = type('Chat', (), {'id': 0})
    fake_msg = FakeMessage(prompt)
    reply = await gemini.process_message(fake_msg)
    return reply.strip()

def get_random_reply_sync(context_messages: Optional[List[str]] = None) -> str:
    # Для сумісності з sync-кодом (наприклад, якщо викликається не з async context)
    import asyncio
    coro = get_random_reply(context_messages)
    if inspect.iscoroutine(coro):
        return asyncio.run(coro)
    return coro
