# 🤖 Гряг-бот v3.2 - Gemini Context Enhanced

## 📦 Продакшн архів: `gryag-bot-gemini-context-enhanced-v3.2-20250628.zip`

### 🎯 Ключові покращення версії 3.2

#### 🚀 **Gemini 2.5 Flash контекст до 1M токенів**
- **РАНІШЕ**: 10,000 символів (~5,000 токенів, 0.5% від доступного)
- **ТЕПЕР**: До 800,000 токенів (200x покращення!)
- Новий модуль `token_counter.py` для точної оцінки токенів
- Підтримка української мови з коефіцієнтом 1.5

#### 🧠 **Розумне стискання контексту**
- Динамічне стискання за токенами (не символами)
- Збереження важливої інформації через LLM
- Автоматична оптимізація для максимального контексту

#### ⚙️ **Нові конфігурації**
```bash
BOT_MAX_CONTEXT_TOKENS=800000    # Максимум токенів для Gemini
BOT_CONTEXT_CHAR_ESTIMATE=600    # Символів на токен (українська)
BOT_TOKENS_PER_CHAR=0.0017       # Токенів на символ
```

### 📁 Що включено в архів

#### 🎯 **Основні модулі**
- `bot/modules/token_counter.py` - **НОВИЙ** модуль підрахунку токенів
- `bot/modules/enhanced_behavior.py` - Оновлений з підтримкою токенів
- `bot/modules/gemini_enhanced.py` - Інтеграція з 1M контекстом
- `bot/bot_config.py` - Нові параметри токенів

#### 🐳 **Docker & Deployment**
- `Dockerfile` та `docker-compose.yml`
- `docker-compose.prod.yml` для продакшну
- `deploy.sh` та `Makefile`

#### 🧪 **Тестування**
- `test_context_tokens.py` - **НОВИЙ** тест токенів
- Всі існуючі тести з async підтримкою
- Unit тести для критичних модулів

#### 📚 **Документація**
- `GEMINI_CONTEXT_ENHANCEMENT_REPORT.md` - Детальний звіт
- `RELEASE_NOTES_v3.2.md` - Релізні нотатки
- `QUICK_START_v3.2.md` - Швидкий старт

### 🚀 Швидкий старт

#### 1️⃣ **Розпакувати архів**
```bash
unzip gryag-bot-gemini-context-enhanced-v3.2-20250628.zip
cd gryag-bot
```

#### 2️⃣ **Налаштувати змінні**
```bash
cp .env.sample .env
# Відредагувати .env з вашими токенами
```

#### 3️⃣ **Запустити з Docker**
```bash
docker-compose up -d
```

#### 4️⃣ **Або локально**
```bash
pip install -r requirements.txt
python start.py
```

### 🔧 Критичні змінні середовища

```bash
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Gemini API
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.0-flash-exp

# НОВІ параметри токенів
BOT_MAX_CONTEXT_TOKENS=800000
BOT_CONTEXT_CHAR_ESTIMATE=600
BOT_TOKENS_PER_CHAR=0.0017

# Адмін
BOT_ADMIN_ID=your_telegram_id
```

### 📊 Результати тестування

```
✅ test_token_estimation_ukrainian - Оцінка українських токенів
✅ test_token_estimation_mixed - Змішана мова
✅ test_context_compression_tokens - Стискання за токенами
✅ test_gemini_integration_tokens - Інтеграція з Gemini
✅ test_behavior_token_limits - Ліміти поведінки

🎯 Покращення контексту: 200x (з 5,000 до 800,000 токенів)
```

### 🎯 Використання в продакшні

#### 🐳 **Docker Compose (рекомендовано)**
```bash
# Продакшн конфігурація
docker-compose -f docker-compose.prod.yml up -d

# Перегляд логів
docker-compose logs -f pomiyka-bot
```

#### 📊 **Моніторинг**
```bash
# Здоров'я бота
curl http://localhost:8080/health

# Статистика
/stats - в телеграмі
/analytics - аналітика чатів
```

### 🔄 Міграція з попередніх версій

#### 1. **Бекап даних**
```bash
# Зберегти дані
cp -r data/ data_backup/
```

#### 2. **Оновити конфігурацію**
```bash
# Додати нові змінні в .env
BOT_MAX_CONTEXT_TOKENS=800000
BOT_CONTEXT_CHAR_ESTIMATE=600
BOT_TOKENS_PER_CHAR=0.0017
```

#### 3. **Запустити тести**
```bash
python -m pytest test_context_tokens.py -v
```

### 🆘 Підтримка та документація

- 📖 **Детальний звіт**: `GEMINI_CONTEXT_ENHANCEMENT_REPORT.md`
- 🚀 **Швидкий старт**: `QUICK_START_v3.2.md`
- 📝 **Релізні нотатки**: `RELEASE_NOTES_v3.2.md`
- 🔧 **Конфігурація**: `bot_config.py`

### 🏆 Основні досягнення v3.2

1. **200x покращення контексту** - з 5K до 800K токенів
2. **Підтримка української мови** - спеціальні коефіцієнти
3. **Розумне стискання** - зберігає важливу інформацію
4. **Повна зворотна сумісність** - без ламання API
5. **Продакшн готовність** - Docker, тести, моніторинг

---

**🎉 Готово до продакшн використання!**
- Архів: `gryag-bot-gemini-context-enhanced-v3.2-20250628.zip` (306KB)
- Дата: 28 червня 2025
- Версія: v3.2 Gemini Context Enhanced
