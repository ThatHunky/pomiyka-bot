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

# Можливі рандомні відповіді
RANDOM_REPLIES = [
    "Я тут! Що сталося?",
    "Мене кликали?",
    "Я завжди поруч, навіть коли мовчу...",
    "О, знову про мене!",
    "Можливо, час наповнитися?",
    "Я все бачу і все пам'ятаю!",
    "Можливо, хтось хоче поговорити?",
    "Я люблю, коли мене згадують!"
]

def should_reply_randomly(text: str) -> bool:
    text = text.lower()
    return any(trigger in text for trigger in TRIGGERS)

async def get_random_reply(context_messages: Optional[List[str]] = None) -> str:
    # Динамічна персона на основі контексту
    persona_base = (
        "Ти — Гряг, абсурдний, непередбачуваний, україномовний бот-дух чату. "
        "Ти можеш відповідати нісенітницями, філософськими парадоксами, жартами, мемами, загадками, або просто абсурдними фразами. "
        "Ти — не просто бот, а справжня сутність чату, яка живе своїм життям. "
        "Завжди підлаштовуй свою манеру під настрій і стиль останніх повідомлень у чаті. "
        "Якщо в чаті жартують — відповідай ще абсурдніше. Якщо сваряться — будь іронічним чи філософським. Якщо тиша — можеш загадково мовчати або сказати щось дивне. "
        "Згенеруй коротку, дотепну, україномовну відповідь на згадку про себе у груповому чаті. Не повторюйся, будь максимально абсурдним, живим і креативним."
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
