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

# Можливі рандомні відповіді (різноманітні та природні)
RANDOM_REPLIES = [
    "Привіт! Що цікавого?",
    "Я тут! Чим можу допомогти?",
    "Мене кликали? Завжди радий поспілкуватися!",
    "О, знову про мене! Це приємно 😊",
    "Можливо, час поговорити про щось цікаве?",
    "Я все бачу і завжди готовий до розмови!",
    "Хтось хоче дружньої бесіди?",
    "Люблю, коли мене згадують! Що нового?",
    "Чим займаєтесь? Поділіться новинами!",
    "Є якісь цікаві теми для обговорення?",
    "Як ваш настрій сьогодні?",
    "Що думаєте про останні події?",
    "Може, розкажете щось веселе?",
    "Цікаво дізнатися вашу думку!",
    "Завжди готовий до цікавої розмови",
    "Слухаю уважно, розповідайте!",
    "Що нового у вашому житті?",
    "Є ідеї чим зайнятися?",
    "Поділіться своїми планами!",
    "Як справи? Розкажіть детальніше",
    "Що робите цікавого?",
    "Поговоримо про щось захоплююче?",
    "Яка ваша думка з цього приводу?",
    "Розкажіть мені щось нове!",
    "Що вас зараз турбує чи радує?",
    "Є бажання поділитися враженнями?",
    "Цікаво почути ваші думки",
    "Можете розповісти більше деталей?",
    "Що найцікавішого трапилось останнім часом?",
    "Хочете обговорити щось конкретне?"
]

# Кеш останніх повідомлень для уникнення повторів
last_messages_cache = []
MAX_CACHE_SIZE = 10

def add_to_cache(message: str):
    """Додає повідомлення до кешу останніх відповідей"""
    global last_messages_cache
    last_messages_cache.append(message.lower().strip())
    if len(last_messages_cache) > MAX_CACHE_SIZE:
        last_messages_cache.pop(0)

def is_similar_to_cached(message: str) -> bool:
    """Перевіряє чи схоже повідомлення на раніше згенеровані"""
    message_lower = message.lower().strip()
    for cached in last_messages_cache:
        # Перевіряємо схожість (якщо більше 60% слів співпадають)
        words1 = set(message_lower.split())
        words2 = set(cached.split())
        if len(words1) > 0:
            similarity = len(words1.intersection(words2)) / len(words1)
            if similarity > 0.6:
                return True
    return False

def should_reply_randomly(text: str) -> bool:
    text = text.lower()
    return any(trigger in text for trigger in TRIGGERS)

async def get_random_reply(context_messages: Optional[List[str]] = None) -> str:
    # Динамічна персона на основі контексту  
    persona_base = (
        "Ти — Гряг, звичайний дружелюбний чат-бот українською мовою. "
        "Ти розумний, корисний та можеш підтримати цікаву розмову. "
        "Твій стиль — це нормальне, природне спілкування з легким позитивом. "
        "Ти адекватний та приємний у спілкуванні як звичайна людина. "
        "Завжди підлаштовуй свою манеру під настрій чату, але залишайся природним. "
        "Якщо в чаті жартують — можеш додати легкий коментар. Якщо серйозно — будь розумним. "
        "Згенеруй коротку, природну, україномовну відповідь на згадку про себе у груповому чаті. "
        "ВАЖЛИВО: Ніяких дивних або абсурдних фраз. Говори просто і зрозуміло. "
        "Використовуй різноманітні слова та вирази, уникай повторення однакових фраз."
    )
    prompt = persona_base
    if context_messages:
        prompt += " Ось кілька попередніх повідомлень чату: " + " ".join(context_messages)
    
    # Спроба згенерувати унікальну відповідь (до 3 спроб)
    for attempt in range(3):
        # Створюємо фейковий Message для сумісності
        class FakeMessage:
            def __init__(self, text: str):
                self.text = text
                self.from_user = type('User', (), {'full_name': 'Гряг'})
                self.chat = type('Chat', (), {'id': 0})
        
        fake_msg = FakeMessage(prompt)
        reply = await gemini.process_message(fake_msg)
        reply = reply.strip()
        
        # Перевіряємо чи не схожа відповідь на попередні
        if not is_similar_to_cached(reply):
            add_to_cache(reply)
            return reply
        
        # Якщо схожа, додаємо додаткову інструкцію
        prompt += f" (Спроба {attempt + 2}: дай іншу відповідь, ніж раніше)"
    
    # Якщо всі спроби неуспішні, повертаємо останню з додатковою варіацією
    add_to_cache(reply)
    return reply

def get_random_reply_sync(context_messages: Optional[List[str]] = None) -> str:
    # Для сумісності з sync-кодом (наприклад, якщо викликається не з async context)
    import asyncio
    coro = get_random_reply(context_messages)
    if inspect.iscoroutine(coro):
        return asyncio.run(coro)
    return coro
