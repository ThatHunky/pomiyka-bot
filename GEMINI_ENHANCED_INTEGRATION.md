# Покращена інтеграція з Gemini API

## Огляд

Проект тепер використовує значно покращену інтеграцію з Gemini API, що забезпечує:
- Сучасну REST API схему з повною підтримкою всіх можливостей Gemini (v1beta - найостанніша версія з новими функціями)
- Розумну обробку контексту та стиснення
- Кастомні system instructions та налаштування
- Rate limiting та кешування
- Статистику та моніторинг
- Підготовку до multimodal та structured output

## Архітектура

### Основні модулі

1. **`gemini_enhanced.py`** - Основний клієнт з повною підтримкою Gemini API
2. **`gemini.py`** - Обгортка для зворотної сумісності зі старим кодом
3. **Інтеграція в `main.py`** - Використання покращених можливостей в основному циклі бота

### Схема взаємодії

```
main.py → gemini.py (wrapper) → gemini_enhanced.py → Gemini API
```

## Ключові можливості

### 1. System Instructions

Тепер підтримуються системні інструкції для кращої персоналізації:

```python
# В .env
GEMINI_SYSTEM_INSTRUCTION="Ви дружелюбний українськомовний бот"

# Програмно
client = await get_client()
response = await client.generate_content(
    "Привіт!", 
    custom_instruction="Відповідай коротко та дружелюбно"
)
```

### 2. Контекстні режими

Розумна обробка контексту залежно від ситуації:

- `"normal"` - Стандартний режим з повним контекстом
- `"minimal"` - Мінімальний контекст для швидких відповідей
- `"guidance"` - Режим порад з акцентом на допомогу
- `"humor"` - Режим гумору з додатковими інструкціями для жартів
- `"clarification"` - Режим пояснень

### 3. Кастомні налаштування генерації

```python
config = GenerationConfig(
    temperature=0.7,        # Креативність (0.0-2.0)
    max_output_tokens=1000, # Максимум токенів відповіді
    top_p=0.8,             # Nucleus sampling
    top_k=40,              # Top-K sampling
    stop_sequences=["END"], # Послідовності зупинки
    thinking_config=ThinkingConfig(
        include_thoughts=False,
        thinking_budget=1024
    )
)
```

### 4. Налаштування безпеки

```python
safety_settings = [
    SafetySetting(HarmCategory.HARASSMENT, HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE),
    SafetySetting(HarmCategory.DANGEROUS_CONTENT, HarmBlockThreshold.BLOCK_ONLY_HIGH)
]
```

### 5. Rate Limiting

Автоматичне обмеження частоти запитів:
- Відстежування RPM (запитів на хвилину)
- Експоненціальна затримка при перевищенні лімітів
- Статистика використання API

### 6. Кешування

Інтелектуальне кешування для оптимізації:
- Кеш ідентичних запитів
- TTL для кеш-записів
- Статистика cache hits/misses

## Налаштування через .env

### Версії API

Gemini API має кілька версій:
- `v1` - стабільна версія з базовими можливостями
- `v1beta` - найостанніша версія з новими функціями (за замовчуванням)
- `v1alpha` - експериментальна версія (не рекомендується для production)

SDK за замовчуванням використовує `v1beta`, що забезпечує доступ до всіх останніх можливостей включаючи:
- Function calling
- Generate Answer
- Semantic retriever
- Розширені safety settings
- Thinking mode

```bash
# Основні параметри
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_VERSION=v1beta

# System instructions
GEMINI_SYSTEM_INSTRUCTION=Ви дружелюбний українськомовний чат-бот

# Генерація контенту
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=1000
GEMINI_TOP_P=0.8
GEMINI_TOP_K=40

# Thinking mode
GEMINI_ENABLE_THINKING=false
GEMINI_THINKING_BUDGET=1024

# Безпека
GEMINI_SAFETY_HARASSMENT=BLOCK_MEDIUM_AND_ABOVE
GEMINI_SAFETY_HATE_SPEECH=BLOCK_MEDIUM_AND_ABOVE
GEMINI_SAFETY_SEXUALLY_EXPLICIT=BLOCK_MEDIUM_AND_ABOVE
GEMINI_SAFETY_DANGEROUS_CONTENT=BLOCK_MEDIUM_AND_ABOVE

# Кешування та rate limiting
GEMINI_ENABLE_CACHE=true
GEMINI_CACHE_TTL=3600
GEMINI_RATE_LIMIT_RPM=60

# Structured output (майбутнє)
GEMINI_ENABLE_STRUCTURED_OUTPUT=false
GEMINI_RESPONSE_MIME_TYPE=text/plain
```

## API Usage

### Базове використання (зворотна сумісність)

```python
from bot.modules import gemini
from bot.modules.utils import FakeMessage

# Старий спосіб все ще працює
message = FakeMessage("Привіт!", chat_id=123, user_name="Користувач")
response = await gemini.process_message(message)
```

### Покращене використання

```python
from bot.modules import gemini

# З кастомною інструкцією тону
response = await gemini.process_message(
    message, 
    tone_instruction="Будь веселим та використовуй емодзі"
)

# Зі статистикою
stats = await gemini.get_gemini_stats()
print(f"Запитів: {stats['total_requests']}, Токенів: {stats['total_tokens']}")
```

### Прямий доступ до enhanced client

```python
from bot.modules.gemini_enhanced import get_client, GenerationConfig

# Отримуємо клієнт
client = await get_client()

# Кастомна генерація
config = GenerationConfig(temperature=0.3, max_output_tokens=100)
response = await client.generate_content(
    "Коротка відповідь про погоду",
    custom_config=config,
    context_type="minimal"
)
```

## Інтеграція в боті

### Основний цикл (main.py)

Бот автоматично використовує покращені можливості:

1. **Розумна обробка контексту** - `enhanced_behavior.py` генерує рекомендації
2. **Тон інструкції** - Додаються автоматично залежно від ситуації
3. **Стиснення контексту** - Великі контексти стискаються автоматично
4. **Rate limiting** - Захист від перевантаження API

### Спонтанні повідомлення

```python
# У main.py
spontaneous_prompt = enhanced_behavior.get_spontaneous_prompt_based_on_trends(chat_id)
fake_msg = FakeMessage(spontaneous_prompt, chat_id, PERSONA['name'])
reply = await gemini.process_message(fake_msg)
await safe_reply(message, f"💭 {reply}")
```

### Команди адміністратора

```python
# У management.py
prompt = "Ти — Гряг, дружелюбний бот..."
fake_msg = FakeMessage(prompt)
reply = await process_message(fake_msg)  # Автоматично використовує enhanced client
```

## Статистика та моніторинг

### Основні метрики

```python
stats = await gemini.get_gemini_stats()
# {
#     'total_requests': 1523,
#     'successful_requests': 1501,
#     'failed_requests': 22,
#     'total_tokens': 45690,
#     'cache_hits': 89,
#     'cache_misses': 1434,
#     'average_response_time': 1.23,
#     'rate_limited_requests': 5
# }
```

### Кеш статистика

```python
from bot.modules.gemini_enhanced import get_cache_stats
cache_stats = await get_cache_stats()
# {
#     'hits': 89,
#     'misses': 1434,
#     'hit_rate': 0.058,
#     'total_entries': 245,
#     'memory_usage': '1.2MB'
# }
```

## Налагодження та логування

### Рівні логування

```python
import logging
logging.getLogger('gemini_enhanced').setLevel(logging.DEBUG)
```

### Приклади логів

```
INFO:gemini_enhanced:API запит: model=gemini-2.5-flash, tokens=123, context_type=normal
DEBUG:gemini_enhanced:Використано кеш для запиту hash=abc123
WARNING:gemini_enhanced:Rate limit досягнуто, чекаємо 2.3 секунди
ERROR:gemini_enhanced:API помилка: 429 Too Many Requests
```

## Майбутні можливості

### Structured Output (підготовлено)

```python
# Готово до використання, коли буде потрібно
schema = {
    "type": "object",
    "properties": {
        "mood": {"type": "string"},
        "response": {"type": "string"}
    }
}

response = await gemini.generate_structured_response(
    "Проаналізуй настрій повідомлення",
    schema
)
```

### Multimodal (підготовлено)

```python
# Архітектура готова для зображень/аудіо
response = await client.generate_content(
    "Опиши це зображення",
    media_files=[{"type": "image", "data": image_data}]
)
```

## Тестування

### Інтеграційні тести

```bash
# Запуск тестів
python -m pytest test_integration_gemini.py -v

# Окремі тести
python -m pytest test_integration_gemini.py::test_gemini_integration -v
```

### Ручне тестування

```bash
# Запуск бота з дебаг режимом
python -m bot.main
```

## Безпека та обмеження

### API ключі

- Використовуйте `.env` файл для зберігання ключів
- Ніколи не комітьте `.env` в git
- Регулярно ротуйте API ключі

### Rate Limiting

- Gemini 2.5 Flash: ~60 RPM безкоштовно
- Автоматичне відстеження лімітів
- Експоненціальне відновлення при перевищенні

### Фільтрація контенту

- Кастомні safety settings
- Автоматична фільтрація шкідливого контенту
- Логування заблокованих запитів

## Вирішення проблем

### Часті помилки

1. **429 Too Many Requests** - Досягнуто rate limit, зачекайте
2. **403 Forbidden** - Перевірте API ключ
3. **400 Bad Request** - Перевірте формат запиту
4. **SAFETY** - Контент заблоковано safety фільтрами

### Діагностика

```python
# Перевірка з'єднання
from bot.modules.gemini_enhanced import test_api_connection
success = await test_api_connection()

# Детальна статистика
stats = await gemini.get_gemini_stats()
print(json.dumps(stats, indent=2))
```

## Заключення

Покращена інтеграція з Gemini API забезпечує:
- Сучасну архітектуру з повною підтримкою можливостей
- Зворотну сумісність зі старим кодом
- Розумну обробку контексту та оптимізацію
- Готовність до майбутніх розширень (multimodal, structured output)
- Надійність та моніторинг

Бот тепер має значно кращі можливості для генерації відповідей, адаптації до контексту та ефективного використання API ресурсів.
