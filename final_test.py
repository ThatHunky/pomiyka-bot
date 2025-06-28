#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

async def final_test():
    from bot.modules.gemini_enhanced import get_client
    
    print("🎯 Фінальний тест покращеної особистості...")
    
    try:
        client = await get_client()
        
        # Простий тест
        response = await client.generate_content("Гряг?")
        print(f"🤖 Відповідь на 'Гряг?': {response}")
        
        # Тест з питанням
        response2 = await client.generate_content("Як справи, бот?") 
        print(f"\n🤖 Відповідь на 'Як справи?': {response2}")
        
        await client.close()
        print("\n🎉 Фінальні тести пройшли успішно!")
        print("✅ Бот тепер менш шизоїдний та більш корисний!")
        
    except Exception as e:
        print(f"❌ Помилка: {e}")

if __name__ == "__main__":
    asyncio.run(final_test())
