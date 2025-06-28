# Швидкий старт з локальним аналізатором

## Встановлення

### 1. Встановіть залежності

```bash
# Основні залежності (обов'язково)
pip install sentence-transformers>=2.2.2
pip install numpy>=1.24.0
pip install scikit-learn>=1.3.0

# Для кращої обробки української мови (рекомендовано)
pip install spacy>=3.7.0
python -m spacy download uk_core_news_sm
```

### 2. Оновіть .env файл

Додайте в ваш `.env` файл:

```bash
# Локальний аналізатор
BOT_LOCAL_ANALYSIS_ENABLED=true
BOT_LOCAL_MODEL_TYPE=sentence_transformers
BOT_ANALYSIS_BATCH_SIZE=5
BOT_ANALYSIS_CACHE_HOURS=24
BOT_ENHANCED_CONTEXT_ENABLED=true
```

### 3. Протестуйте

```bash
python test_local_analyzer.py
```

## Перевірка роботи

### В Telegram боті:

1. Напишіть: **"Гряг, як справи?"**
   - Бот повинен відповісти більш контекстно

2. Спробуйте технічну тему: **"Гряг, поясни як працює React"**
   - Бот повинен розпізнати технічну тематику

3. Емоційне повідомлення: **"Дуже сумно 😢"**
   - Бот повинен відповісти підтримуючим тоном

### Адмін команди:

- `/health` - статус локального аналізатора
- `/analytics` - аналітика чату

## Налаштування для i5-6500

### Оптимальні значення:

```bash
BOT_ANALYSIS_BATCH_SIZE=5          # Не більше для вашого CPU
BOT_ANALYSIS_CACHE_HOURS=24        # Баланс між якістю та пам'яттю
BOT_LOCAL_MODEL_TYPE=sentence_transformers  # Легший за ollama
```

### Якщо бракує пам'яті:

```bash
BOT_ANALYSIS_BATCH_SIZE=3          # Зменшіть пакет
BOT_ANALYSIS_CACHE_HOURS=12        # Зменшіть кеш
```

### Якщо повільно працює:

```bash
BOT_LOCAL_ANALYSIS_ENABLED=false   # Тимчасово вимкніть
# Або
BOT_ANALYSIS_BATCH_SIZE=2          # Мінімальний пакет
```

## Результат

Після включення локального аналізатора ваш бот буде:

✅ **Розумніше** визначати емоції та теми  
✅ **Краще** розуміти контекст розмов  
✅ **Природніше** відповідати на повідомлення  
✅ **Ефективніше** використовувати Gemini API  

## Моніторинг

Дивіться логи на предмет:

```
✅ Sentence Transformer модель завантажена
✅ spaCy українська модель завантажена  
📊 Analysis took 45ms, method: enhanced_local
```

Якщо бачите `method: regex_fallback` - локальний аналізатор не працює.
