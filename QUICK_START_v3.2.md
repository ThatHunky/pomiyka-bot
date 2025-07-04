# 🚀 Гряг-бот v3.2 - Gemini Context Enhanced

**Найбільше покращення в історії проекту! Контекстне вікно збільшено в 200 разів!**

---

## 📊 **ОСНОВНІ ПОКРАЩЕННЯ**

- 🚀 **Контекст:** 10,000 символів → **2,000,000 символів** (200x)
- 🧮 **Токени:** точний підрахунок для української мови
- 🎯 **Розумне стискання:** збереження важливих повідомлень
- ⚙️ **Нова конфігурація:** підтримка Gemini 2.5 Flash (1M токенів)

---

## ⚡️ **ШВИДКИЙ СТАРТ**

```bash
# 1. Розпакувати архів
unzip gryag-bot-gemini-context-enhanced-v3.2-20250628.zip
cd gryag-bot/

# 2. Налаштувати токени
cp .env.sample .env
# Додати ваші токени в .env:
# TELEGRAM_BOT_TOKEN=your_bot_token
# GEMINI_API_KEY=your_gemini_key

# 3. Запустити
docker-compose up -d
```

---

## 🔧 **НОВІ ЗМІННІ СЕРЕДОВИЩА**

```bash
# Gemini 2.5 Flash токени (НОВІ):
BOT_MAX_CONTEXT_TOKENS=800000          # 80% від 1M токенів
BOT_CONTEXT_CHAR_ESTIMATE=2000000      # ~2M символів
BOT_TOKENS_PER_CHAR=0.4                # Коефіцієнт для української

# Старий параметр (сумісність):
BOT_MAX_CONTEXT_SIZE=10000             # ЗАСТАРІЛИЙ
```

---

## 🧪 **ТЕСТУВАННЯ**

```bash
# Тест нових можливостей:
python test_context_tokens.py

# Валідація конфігурації:
python -m bot.modules.config_validator
```

---

## 📁 **СТРУКТУРА ПРОЕКТУ**

```
gryag-bot-v3.2/
├── bot/
│   ├── main.py                    # Головний файл
│   ├── bot_config.py             # Оновлена конфігурація
│   └── modules/
│       ├── token_counter.py      # 🆕 Підрахунок токенів
│       ├── enhanced_behavior.py  # Покращена поведінка
│       ├── gemini_enhanced.py    # Gemini 2.5 Flash
│       └── ...
├── .env.sample                   # Приклад конфігурації
├── docker-compose.yml           # Docker Compose
├── requirements.txt             # Залежності
└── README.md                    # Цей файл
```

---

## 📈 **РЕЗУЛЬТАТИ**

| Метрика | Було | Стало | Покращення |
|---------|------|-------|------------|
| Контекст | 10K символів | 2M символів | **200x** |
| Токени | ~4K | 800K | **200x** |
| Використання API | 0.5% | 80% | **160x** |

---

## 🎯 **НОВИНКИ v3.2**

### **🧮 token_counter.py:**
- Точна оцінка токенів для української мови
- Розпізнавання типу контенту (код, URL, емодзі)
- Автоматичне визначення мови

### **🎯 Розумне стискання:**
- Пріоритизація важливих повідомлень
- Збереження згадок бота та питань
- Хронологічний порядок

### **⚙️ Покращені ліміти:**
- Rate limiting: 3/хв на чат, 20/хв глобально
- Анти-спам: м'які реакції замість агресивних
- Smart replies: 3% шанс, максимум 2/годину

---

## 🔗 **ДОКУМЕНТАЦІЯ**

- `GEMINI_CONTEXT_ENHANCEMENT_REPORT.md` - детальний звіт
- `RELEASE_NOTES_v3.2.md` - нотатки релізу
- `PRODUCTION_RELEASE_v3.2_REPORT.md` - звіт деплою

---

## 🎉 **ГОТОВО!**

Бот тепер використовує майже повний потенціал Gemini 2.5 Flash з його контекстним вікном у 1 мільйон токенів!

**Покращення в 200 разів - це історичний момент для проекту! 🚀**
