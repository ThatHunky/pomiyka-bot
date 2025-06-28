#!/usr/bin/env python3
import asyncio
import sys
import os

# Додаємо шлях до модулів бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

async def quick_test():
    from bot.modules.gemini_enhanced import get_client
    
    print("🤖 Швидкий тест нової особистості бота...")
    
    try:
        client = await get_client()
        
        # Тест з питанням про кабелі (як у прикладі)
        response = await client.generate_content(
            "Гряг, що думаєш про ці помилки підключення з кабелями?",
            context_type="normal"
        )
        
        print(f"📝 Відповідь бота: {response}")
        print("\n✅ Тест завершено успішно!")
        
        await client.close()
        return True
        
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(quick_test())
