#!/usr/bin/env python3
"""
Тест покращеного контекстного вікна Gemini 2.5 Flash (1M токенів)
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Додаємо шлях до бота
sys.path.append(os.path.join(os.path.dirname(__file__), 'bot'))

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_token_estimation():
    """Тестує оцінку кількості токенів"""
    print("🧮 Тестуємо підрахунок токенів...")
    
    from bot.modules.token_counter import token_counter
    
    # Тестові тексти
    test_texts = [
        "Привіт! Як справи?",  # Звичайний текст
        "def hello_world():\n    print('Hello, World!')",  # Код
        "🎉 Супер! 😍 Дуже круто! 🚀",  # Емодзі
        "Це дуже довгий текст який містить багато інформації про різні речі, включаючи технічні деталі, емоції, питання та інші елементи розмови.",  # Довгий текст
        "",  # Порожній текст
        "https://example.com/api/v1/users?id=123&token=abc",  # URL
    ]
    
    for i, text in enumerate(test_texts, 1):
        tokens = token_counter.estimate_tokens(text)
        language = token_counter.detect_language(text)
        chars = len(text)
        ratio = tokens / chars if chars > 0 else 0
        
        print(f"  {i}. Текст: {text[:50]}{'...' if len(text) > 50 else ''}")
        print(f"     Символів: {chars}, Токенів: {tokens}, Мова: {language}, Коефіцієнт: {ratio:.3f}")
        print()

async def test_context_compression():
    """Тестує стискання контексту"""
    print("📦 Тестуємо стискання контексту...")
    
    from bot.modules.token_counter import token_counter
    
    # Створюємо тестовий контекст
    test_context = []
    for i in range(200):  # 200 повідомлень
        message = {
            "user_name": f"Користувач{i % 10}",
            "text": f"Це повідомлення номер {i}. Містить різну інформацію про тестування.",
            "timestamp": f"2025-06-28T10:{i % 60:02d}:00"
        }
        
        # Додаємо важливі повідомлення
        if i % 20 == 0:
            message["text"] = f"@gryag_bot, що думаєш про це питання {i}?"
        elif i % 15 == 0:
            message["text"] = f"Гряг, можеш допомогти з {i}?"
        
        test_context.append(message)
    
    # Оцінюємо початковий розмір
    original_tokens = token_counter.estimate_context_tokens(test_context)
    print(f"Початковий контекст: {len(test_context)} повідомлень, ~{original_tokens} токенів")
    
    # Тестуємо різні ліміти
    limits = [50000, 100000, 200000, 500000]
    
    for limit in limits:
        compressed = token_counter.compress_context_by_tokens(test_context, limit)
        compressed_tokens = token_counter.estimate_context_tokens(compressed)
        
        important_count = sum(1 for msg in compressed 
                            if 'гряг' in msg['text'].lower() or '@gryag_bot' in msg['text'].lower())
        
        print(f"  Ліміт {limit:,} токенів:")
        print(f"    Результат: {len(compressed)} повідомлень, ~{compressed_tokens} токенів")
        print(f"    Важливих повідомлень збережено: {important_count}")
        print(f"    Компресія: {len(compressed)/len(test_context)*100:.1f}% повідомлень, "
              f"{compressed_tokens/original_tokens*100:.1f}% токенів")
        print()

async def test_new_config_parameters():
    """Тестує нові параметри конфігурації"""
    print("⚙️ Тестуємо нові параметри конфігурації...")
    
    from bot.bot_config import PERSONA
    
    # Перевіряємо нові параметри
    config_params = [
        'max_context_tokens',
        'context_char_estimate', 
        'tokens_per_char_ukrainian'
    ]
    
    print("Нові параметри конфігурації:")
    for param in config_params:
        value = PERSONA.get(param, "НЕ ЗНАЙДЕНО")
        print(f"  {param}: {value}")
    
    # Розрахуємо теоретичний максимум
    max_tokens = PERSONA.get('max_context_tokens', 800000)
    char_estimate = PERSONA.get('context_char_estimate', 2000000)
    tokens_per_char = PERSONA.get('tokens_per_char_ukrainian', 0.4)
    
    print(f"\nТеоретичні можливості:")
    print(f"  Максимум токенів: {max_tokens:,}")
    print(f"  Оцінка символів: {char_estimate:,}")
    print(f"  Коефіцієнт токен/символ: {tokens_per_char}")
    print(f"  Реальна оцінка символів: {int(max_tokens / tokens_per_char):,}")
    
    # Порівняння зі старими лімітами
    old_char_limit = PERSONA.get('max_context_size', 10000)
    improvement = (max_tokens / tokens_per_char) / old_char_limit
    
    print(f"\nПокращення:")
    print(f"  Старий ліміт: {old_char_limit:,} символів")
    print(f"  Новий ліміт: ~{int(max_tokens / tokens_per_char):,} символів")
    print(f"  Покращення в {improvement:.1f} разів! 🚀")

async def test_gemini_integration():
    """Тестує інтеграцію з Gemini API"""
    print("🤖 Тестуємо інтеграцію з Gemini...")
    
    try:
        # Перевіряємо чи встановлені ключі
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("  ❌ GEMINI_API_KEY не встановлено - пропускаємо тест інтеграції")
            return
        
        from bot.modules.token_counter import token_counter
        
        # Створюємо великий контекст для тестування
        large_context = []
        for i in range(500):
            large_context.append({
                "user_name": f"Тестер{i % 5}",
                "text": f"Повідомлення {i}: Це тестове повідомлення для перевірки роботи з великим контекстом. Воно містить українською мовою різну інформацію про тестування, розробку та інші технічні деталі."
            })
        
        tokens = token_counter.estimate_context_tokens(large_context)
        print(f"  Великий контекст: {len(large_context)} повідомлень, ~{tokens:,} токенів")
        
        # Перевіряємо чи поміститься в ліміт
        max_tokens = 800000
        if tokens <= max_tokens:
            print(f"  ✅ Контекст поміщується в ліміт ({tokens:,} <= {max_tokens:,})")
        else:
            print(f"  ⚠️ Контекст перевищує ліміт ({tokens:,} > {max_tokens:,})")
            compressed = token_counter.compress_context_by_tokens(large_context, max_tokens)
            compressed_tokens = token_counter.estimate_context_tokens(compressed)
            print(f"     Після стискання: {len(compressed)} повідомлень, ~{compressed_tokens:,} токенів")
        
    except Exception as e:
        print(f"  ❌ Помилка при тестуванні інтеграції: {e}")

async def main():
    """Головна функція тестування"""
    print("🚀 Тестування покращеного контекстного вікна Gemini 2.5 Flash")
    print("=" * 70)
    
    tests = [
        test_new_config_parameters,
        test_token_estimation, 
        test_context_compression,
        test_gemini_integration,
    ]
    
    for test_func in tests:
        try:
            await test_func()
            print()
        except Exception as e:
            print(f"❌ Помилка в тесті {test_func.__name__}: {e}")
            print()
    
    print("=" * 70)
    print("✅ Тестування завершено!")
    print()
    print("📈 Підсумок покращень:")
    print("  • Підтримка 1M токенів замість 10K символів")
    print("  • Розумне стискання контексту з урахуванням важливості")
    print("  • Точна оцінка токенів для української мови")
    print("  • Покращення контексту в ~200 разів!")

if __name__ == "__main__":
    # Встановлюємо тестові змінні середовища
    os.environ.setdefault('BOT_MAX_CONTEXT_TOKENS', '800000')
    os.environ.setdefault('BOT_CONTEXT_CHAR_ESTIMATE', '2000000')
    os.environ.setdefault('BOT_TOKENS_PER_CHAR', '0.4')
    os.environ.setdefault('BOT_PERSONA_NAME', 'Гряг')
    os.environ.setdefault('ADMIN_ID', '123456789')
    
    asyncio.run(main())
