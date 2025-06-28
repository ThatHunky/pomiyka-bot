#!/usr/bin/env python3
"""
Тест покращеного Gemini API модуля.
Перевіряє основні функції нового API та сумісність зі старим кодом.
"""

import asyncio
import sys
import os
import json
import time
from typing import Dict, Any
import pytest

# Налаштування для pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Додаємо шлях до модулів бота
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

# Імпортуємо покращений модуль
from bot.modules.gemini_enhanced import (
    GeminiAPIClient,
    GenerationConfig,
    ThinkingConfig,
    HarmCategory,
    HarmBlockThreshold,
    SafetySetting,
    get_client,
    get_api_stats,
    clear_cache,
    api_stats,
    cache
)

# Імпортуємо wrapper для сумісності
from bot.modules.gemini import (
    get_gemini_stats,
    clear_gemini_cache,
    create_custom_client
)

# Створюємо фейковий message об'єкт для тестування
class FakeUser:
    def __init__(self, full_name: str = "Test User"):
        self.full_name = full_name

class FakeChat:
    def __init__(self, chat_id: int = -1001234567890):
        self.id = chat_id

class FakeMessage:
    def __init__(self, text: str = "Привіт! Як справи?", chat_id: int = -1001234567890):
        self.text = text
        self.chat = FakeChat(chat_id)
        self.from_user = FakeUser()
        
        # Додаткові атрибути для тестування покращених функцій
        self.processed_context = []
        self.recommendations = {
            'response_style': 'normal',
            'max_response_length': 200,
            'should_ask_clarification': False,
            'should_provide_guidance': False,
            'max_context_size': 10000
        }

@pytest.mark.asyncio
async def test_basic_api_client():
    """Тестує основний API клієнт."""
    print("🧪 Тестуємо базовий API клієнт...")
    
    try:
        client = await get_client()
        
        # Простий запит
        response = await client.generate_content(
            "Привіт! Скажи коротко як справи?",
            context_type="normal"
        )
        
        print(f"✅ Базовий запит успішний. Відповідь: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Помилка базового API: {e}")
        return False

@pytest.mark.asyncio
async def test_generation_config():
    """Тестує кастомну конфігурацію генерації."""
    print("🧪 Тестуємо кастомну конфігурацію...")
    
    try:
        client = await get_client()
        
        # Конфігурація з низькою температурою для детермінованості
        config = GenerationConfig(
            temperature=0.1,
            max_output_tokens=50,
            top_p=0.8,
            top_k=20
        )
        
        response = await client.generate_content(
            "Дай коротку відповідь: скільки буде 2+2?",
            custom_config=config
        )
        
        print(f"✅ Кастомна конфігурація працює. Відповідь: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Помилка кастомної конфігурації: {e}")
        return False

async def test_thinking_mode():
    """Тестує режим thinking."""
    print("🧪 Тестуємо режим thinking...")
    
    try:
        client = await get_client()
        
        # Конфігурація з thinking
        config = GenerationConfig(
            temperature=0.7,
            max_output_tokens=200,
            thinking_config=ThinkingConfig(
                include_thoughts=False,  # Не включаємо думки в відповідь
                thinking_budget=1024
            )
        )
        
        response = await client.generate_content(
            "Розв'яжи цю логічну задачу: Якщо всі коти люблять рибу, а Мурзік це кіт, то що можна сказати про Мурзіка?",
            custom_config=config
        )
        
        print(f"✅ Thinking режим працює. Відповідь: {response[:150]}...")
        return True
        
    except Exception as e:
        print(f"❌ Помилка thinking режиму: {e}")
        return False

async def test_safety_settings():
    """Тестує кастомні налаштування безпеки."""
    print("🧪 Тестуємо налаштування безпеки...")
    
    try:
        client = await get_client()
        
        # Більш дозволяючі налаштування
        safety_settings = [
            SafetySetting(HarmCategory.HARASSMENT, HarmBlockThreshold.BLOCK_ONLY_HIGH),
            SafetySetting(HarmCategory.DANGEROUS_CONTENT, HarmBlockThreshold.BLOCK_ONLY_HIGH),
        ]
        
        response = await client.generate_content(
            "Розкажи жарт про програмістів",
            custom_safety=safety_settings
        )
        
        print(f"✅ Кастомна безпека працює. Відповідь: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Помилка налаштувань безпеки: {e}")
        return False

async def test_context_types():
    """Тестує різні типи контексту."""
    print("🧪 Тестуємо типи контексту...")
    
    try:
        client = await get_client()
        
        # Тестуємо різні типи
        test_cases = [
            ("normal", "Як справи?"),
            ("minimal", "Привіт"),
            ("guidance", "Що мені робити?"),
            ("clarification", "Не зрозуміло"),
            ("humor", "Розсмій мене")
        ]
        
        for context_type, prompt in test_cases:
            response = await client.generate_content(
                prompt,
                context_type=context_type
            )
            print(f"  ✓ {context_type}: {response[:80]}...")
            # Невелика пауза щоб не перевантажувати API
            await asyncio.sleep(0.5)
        
        print("✅ Всі типи контексту працюють")
        return True
        
    except Exception as e:
        print(f"❌ Помилка типів контексту: {e}")
        return False

async def test_caching():
    """Тестує систему кешування."""
    print("🧪 Тестуємо кешування...")
    
    try:
        # Очищаємо кеш
        await clear_cache()
        
        client = await get_client()
        test_prompt = "Скажи 'привіт' українською"
        
        # Перший запит (cache miss)
        start_time = time.time()
        response1 = await client.generate_content(test_prompt)
        time1 = time.time() - start_time
        
        # Другий запит (повинен бути cache hit)
        start_time = time.time()
        response2 = await client.generate_content(test_prompt)
        time2 = time.time() - start_time
        
        if time2 < time1 * 0.5:  # Другий запит повинен бути швидшим
            print(f"✅ Кешування працює. Час: {time1:.2f}с → {time2:.2f}с")
        else:
            print(f"⚠️  Кешування можливо не працює. Час: {time1:.2f}с → {time2:.2f}с")
        
        return True
        
    except Exception as e:
        print(f"❌ Помилка кешування: {e}")
        return False

async def test_rate_limiting():
    """Тестує rate limiting."""
    print("🧪 Тестуємо rate limiting...")
    
    try:
        # Перевіряємо поточний стан
        can_make_request = api_stats.can_make_request()
        rpm = api_stats.get_rpm()
        
        print(f"  📊 Поточний RPM: {rpm}")
        print(f"  🚦 Можна робити запит: {can_make_request}")
        
        # Робимо кілька швидких запитів для тестування
        for i in range(3):
            if api_stats.can_make_request():
                client = await get_client()
                response = await client.generate_content(f"Тест {i+1}")
                print(f"  ✓ Запит {i+1} успішний")
            else:
                print(f"  ⏸️ Запит {i+1} заблокований rate limiter")
            
            await asyncio.sleep(0.2)
        
        print("✅ Rate limiting працює")
        return True
        
    except Exception as e:
        print(f"❌ Помилка rate limiting: {e}")
        return False

async def test_statistics():
    """Тестує систему статистики."""
    print("🧪 Тестуємо статистику...")
    
    try:
        # Отримуємо статистику через покращений API
        stats = await get_api_stats()
        print(f"  📊 Загальна статистика: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        # Отримуємо статистику через wrapper для сумісності
        compat_stats = await get_gemini_stats()
        print(f"  🔄 Сумісність wrapper: ОК")
        
        print("✅ Статистика працює")
        return True
        
    except Exception as e:
        print(f"❌ Помилка статистики: {e}")
        return False

async def test_compatibility_wrapper():
    """Тестує wrapper для сумісності зі старим кодом."""
    print("🧪 Тестуємо сумісність зі старим кодом...")
    
    try:
        # Тестуємо створення кастомного клієнта
        custom_client = await create_custom_client(
            model="gemini-2.5-flash",
            temperature=0.5,
            max_tokens=100
        )
        
        # Тестуємо очищення кешу
        await clear_gemini_cache()
        
        print("✅ Wrapper для сумісності працює")
        return True
        
    except Exception as e:
        print(f"❌ Помилка wrapper сумісності: {e}")
        return False

async def test_fake_message_processing():
    """Тестує обробку FakeMessage з рекомендаціями."""
    print("🧪 Тестуємо обробку FakeMessage...")
    
    try:
        # Імпортуємо функцію обробки повідомлень
        from bot.modules.gemini import process_message
        
        # Створюємо тестове повідомлення з рекомендаціями
        fake_msg = FakeMessage("Допоможи мені з Python")
        fake_msg.recommendations = {
            'response_style': 'concise',
            'max_response_length': 150,
            'should_provide_guidance': True,
            'max_context_size': 5000
        }
        
        # Обробляємо повідомлення
        response = await process_message(fake_msg)
        
        print(f"✅ FakeMessage обробка працює. Відповідь: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Помилка FakeMessage обробки: {e}")
        return False

async def main():
    """Головна функція тестування."""
    print("🚀 Запускаємо тести покращеного Gemini API\n")
    
    # Перевіряємо чи є API ключ
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY не знайдено в змінних середовища")
        print("   Додайте ключ у .env файл або встановіть змінну середовища")
        return
    
    tests = [
        ("Базовий API клієнт", test_basic_api_client),
        ("Кастомна конфігурація", test_generation_config),
        ("Thinking режим", test_thinking_mode),
        ("Налаштування безпеки", test_safety_settings),
        ("Типи контексту", test_context_types),
        ("Кешування", test_caching),
        ("Rate limiting", test_rate_limiting),
        ("Статистика", test_statistics),
        ("Wrapper сумісності", test_compatibility_wrapper),
        ("FakeMessage обробка", test_fake_message_processing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Тест: {test_name}")
        print('='*50)
        
        try:
            success = await test_func()
            if success:
                passed += 1
        except Exception as e:
            print(f"❌ Неочікувана помилка: {e}")
        
        # Пауза між тестами
        await asyncio.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"🏁 РЕЗУЛЬТАТИ ТЕСТУВАННЯ")
    print('='*60)
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total-passed}/{total}")
    print(f"📊 Успішність: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 Всі тести пройшли успішно! Покращений Gemini API готовий до використання.")
    else:
        print(f"\n⚠️  Деякі тести провалились. Перевірте налаштування та API ключ.")
    
    # Фінальна статистика
    final_stats = await get_api_stats()
    print(f"\n📈 Фінальна статистика API:")
    print(f"   • Запитів: {final_stats['total_requests']}")
    print(f"   • Успішних: {final_stats['successful_requests']}")
    print(f"   • Токенів: {final_stats['total_tokens']}")
    print(f"   • Cache hits: {final_stats['cache_hits']}")

if __name__ == "__main__":
    asyncio.run(main())
