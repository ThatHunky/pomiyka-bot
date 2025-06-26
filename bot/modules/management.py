# Модуль для менеджменту (доступно лише адміністратору)
from aiogram.types import Message

async def handle(message: Message):
    from bot.modules.gemini import process_message
    class FakeMessage:
        def __init__(self, text: str):
            self.text = text
            self.from_user = type('User', (), {'full_name': 'Глек'})
            self.chat = type('Chat', (), {'id': 0})
    if message.text == "/stats":
        prompt = (
            "Ти — Глек, абсурдний бот-дух. Відповідай на адмінські команди у стилі абсурду, мемів, парадоксів. "
            "Ось команда: /stats. Відповідь має бути короткою, дотепною, але інформативною."
        )
    else:
        prompt = (
            "Ти — Глек, абсурдний бот-дух. Відповідай на адмінські команди у стилі абсурду, мемів, парадоксів. "
            f"Ось команда: {message.text}. Відповідь має бути короткою, дотепною, але інформативною."
        )
    fake_msg = FakeMessage(prompt)
    reply = await process_message(fake_msg)
    await message.reply(reply)
