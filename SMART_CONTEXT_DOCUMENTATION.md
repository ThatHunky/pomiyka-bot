# Покращена обробка контексту чату - Документація

## Огляд

Модуль `enhanced_behavior.py` тепер включає розумну систему обробки контексту чату, яка запобігає спаму та нонсенсу від бота. Система автоматично аналізує активність в чаті та корегує поведінку бота відповідно.

## Основні функції

### 1. `process_message_with_smart_context()`

**Головна функція** для розумної обробки повідомлень.

```python
result = process_message_with_smart_context(
    message_text="Гряг, що думаєш?",
    chat_id=123,
    context=chat_context,
    recent_messages=recent_msgs
)
```

**Повертає:**
- `should_respond` - чи потрібно відповідати
- `response_tone` - рекомендований тон відповіді
- `spam_analysis` - аналіз рівня спаму
- `context_quality` - якість контексту розмови
- `tone_instruction` - готова інструкція для Gemini
- `recommendations` - рекомендації щодо відповіді

### 2. `analyze_chat_spam_level()`

Аналізує рівень спаму в чаті:

```python
spam_info = analyze_chat_spam_level(chat_id, recent_messages)
```

**Рівні спаму:**
- `low` - нормальна активність
- `medium` - підвищена активність (15-30 повідомлень за 5 хв)
- `high` - спам (30+ повідомлень за 5 хв)

### 3. `compress_context_smartly()`

Розумно стискає великий контекст:

```python
compressed = compress_context_smartly(context, max_context_size=100)
```

**Алгоритм:**
1. Зберігає всі важливі повідомлення (згадки бота, питання, довгі тексти)
2. Додає найновіші звичайні повідомлення до ліміту
3. Сортує за часом

### 4. `analyze_context_quality()`

Оцінює якість контексту розмови:

```python
quality_info = analyze_context_quality(context)
```

**Рівні якості:**
- `high` - когерентна розмова (>70% схожих тем)
- `medium` - середня когерентність (40-70%)
- `poor` - розбитий контекст (<40%)

## Система рекомендацій

Залежно від ситуації в чаті, система генерує рекомендації:

### При спамі:
- Зменшує довжину відповіді (`max_response_length`)
- Змінює стиль на `minimal` або `concise`
- Різко знижує шанс відповіді

### При поганому контексті:
- Додає флаг `should_ask_clarification`
- Встановлює `should_provide_guidance`
- Змінює тон на `направляючий_жарт`

## Інтеграція з основним ботом

### У файлі `main.py`:

```python
from bot.modules.enhanced_behavior import process_message_with_smart_context

async def handle_message(message):
    # Отримати контекст чату
    context = await get_chat_context(message.chat.id)
    recent_messages = context[-20:]  # Останні 20 повідомлень
    
    # Розумна обробка
    analysis = process_message_with_smart_context(
        message.text,
        message.chat.id,
        context,
        recent_messages
    )
    
    # Перевірити чи потрібно відповідати
    if analysis['should_respond']:
        # Використати рекомендації
        recommendations = analysis['recommendations']
        
        if recommendations['response_style'] == 'minimal':
            # Коротка відповідь для спаму
            response = await generate_short_response(
                analysis['tone_instruction']
            )
        else:
            # Звичайна відповідь
            response = await generate_response(
                analysis['tone_instruction'],
                analysis['processed_context']
            )
        
        await message.reply(response)
    
    # Перевірити чи потрібно показати анти-спам повідомлення
    spam_level = analysis['spam_analysis']['spam_level']
    if spam_level in ['medium', 'high']:
        anti_spam_msg = get_anti_spam_message(spam_level)
        if anti_spam_msg and random.random() < 0.3:  # 30% шанс
            await message.reply(anti_spam_msg)
```

## Налаштування

### У файлі `.env`:

```env
# Контроль спаму
BOT_SPAM_THRESHOLD=5          # Повідомлень за хвилину для спаму
BOT_SPAM_TIMEOUT=300          # Таймаут при спамі (секунди)
BOT_SMART_REPLY_CHANCE=0.05   # Базовий шанс відповіді (5%)

# Контекст
BOT_CONTEXT_LIMIT=100         # Максимальний розмір контексту
BOT_MAX_MESSAGE_AGE_MINUTES=60 # Максимальний вік повідомлень

# Автономність
BOT_AUTONOMOUS_MODE=true
BOT_SPONTANEOUS_CHANCE=0.01   # 1% шанс спонтанного повідомлення
BOT_MAX_REPLIES_PER_HOUR=2    # Максимум відповідей на годину
```

## Логування та моніторинг

Система логує важливі події:

```python
# Статистика обробки
stats = get_processing_statistics(chat_id)
print(f"Повідомлень за годину: {stats['messages_last_hour']}")

# Логування обробки
log_context_processing(chat_id, message_count, spam_level, context_quality)
```

## Тестування

Запустіть тест для перевірки:

```bash
python test_smart_context.py
```

## Переваги нової системи

1. **Анти-спам захист** - автоматично виявляє спам та зменшує активність бота
2. **Розумне стиснення контексту** - зберігає важливу інформацію
3. **Адаптивна поведінка** - корегує тон та стиль відповідно до ситуації
4. **Якість контексту** - аналізує когерентність розмови
5. **Гнучкі рекомендації** - система рекомендацій для різних ситуацій
6. **Повне логування** - відстеження для діагностики

## Приклади використання

### Нормальна ситуація:
```
Користувач: "Гряг, як справи?"
Система: should_respond=True, tone="дружелюбний_жарт", length=200
Відповідь: "Привіт! Все супер, дякую що питаєш! 😊"
```

### Ситуація зі спамом:
```
[30 повідомлень за 5 хвилин]
Користувач: "Звичайне повідомлення"
Система: should_respond=False, spam_level="high"
Результат: Бот мовчить або відправляє анти-спам повідомлення
```

### Погана якість контексту:
```
[Хаотичні повідомлення різними темами]
Користувач: "Що думаєш?"
Система: tone="направляючий_жарт", should_provide_guidance=True
Відповідь: "Про що саме? Давайте визначимося з темою 🤔"
```

Ця система значно покращує якість взаємодії бота з користувачами та запобігає спаму і нонсенсу.
