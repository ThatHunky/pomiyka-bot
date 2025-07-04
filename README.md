# 🤖 Гряг-бот

Україномовний дружелюбний Telegram-бот для групових чатів з підтримкою великого контексту та інтеграцією з Gemini Flash 2.5.

## 🎭 Особливості
- **Природна персона**: Гряг — дружелюбний помічник з корисними порадами та легким гумором
- **Покращена Gemini інтеграція**: повна підтримка system instructions, мінімальні safety settings, thinking mode, structured output
- **Розумна обробка контексту**: автоматичне стиснення, адаптивні режими (normal, minimal, guidance, humor)
- **Адекватна поведінка**: підлаштовується під настрій чату, але залишається зрозумілим та корисним
- **Спонтанні повідомлення**: час від часу пише щось корисне від себе, не у відповідь 💭
- **Агресивний анти-спам**: при спамі може сказати "тіха блять, хохли" або ігнорувати
- **Автоматичне сканування**: при додаванні в новий чат автоматично ініціалізується
- **Великий контекст**: запам'ятовує історію на багато днів (SQLite)
- **Кешування та rate limiting**: оптимізоване використання Gemini API з статистикою
- **Медіа-підтримка**: стікери, фото, аудіо, відео з корисними описами
- **Реакції**: автоматично ставить емоджі-реакції на повідомлення (👍❤️🔥🤔)
- **Розумні ліміти**: не більше 3 відповідей на годину, паузи між спонтанними повідомленнями
- **Рандомні відповіді**: реагує на згадки свого імені (@gryag_bot, грягік тощо)
- **Імпорт історії**: можна завантажити chat.json з Telegram Desktop
- **Docker-ready**: готовий до деплою в контейнері
- **Модульна архітектура**: легко розширювати

## 🛠 Техстек
- Python 3.12+
- aiogram 3.4+ (Telegram Bot API)
- aiohttp (HTTP-клієнт)
- SQLite (контекст та історія)
- **Gemini 2.5 Flash** ⭐ (безкоштовний AI/NLP)
- python-dotenv (конфігурація)

### 💎 Про Gemini API ліміти

**Безкоштовні моделі (Free Tier):**
- ✅ Gemini 2.5 Flash (рекомендовано)
- ✅ Gemini 2.0 Flash 
- ✅ Gemini 1.5 Flash/Pro
- ❌ Gemini 2.5 Pro (платна)

**Обмеження Free Tier:**
- ~15-60 запитів/хвилину (RPM)
- Денні ліміти (RPD)
- Google використовує дані для покращення

**Оптимізації в боті:**
- Анти-спам система з лімітами
- Локальний кеш контексту (SQLite)
- Абсурдні префікси для медіа (економія токенів)

## 🚀 Швидкий старт

1. **Клонуйте репозиторій**:
   ```bash
   git clone <repo-url>
   cd pomiyka-bot
   ```

2. **Встановіть залежності**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Налаштуйте конфігурацію**:
   ```bash
   cp .env.sample .env
   # Відредагуйте .env — додайте токени та налаштування
   ```

4. **Запустіть бота**:
   ```bash
   python start.py
   ```

## 🤖 Покращена Gemini інтеграція

Бот використовує сучасну інтеграцію з Gemini API v1beta (найостанніша версія) з повною підтримкою всіх можливостей:

### Ключові можливості:
- **System Instructions**: кастомні системні інструкції для кращої персоналізації
- **Контекстні режими**: normal, minimal, guidance, humor, clarification
- **Safety Settings**: налаштовувані фільтри безпеки
- **Thinking Mode**: покращена аналітичність відповідей
- **Rate Limiting**: автоматичне обмеження для оптимального використання API
- **Кешування**: інтелектуальне кешування ідентичних запитів
- **Статистика**: детальний моніторинг використання API
- **Structured Output**: готовність до JSON відповідей
- **Multimodal**: підготовка до роботи з зображеннями

### Налаштування в .env:
```bash
# Основні параметри Gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_VERSION=v1beta
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=1000

# System instructions
GEMINI_SYSTEM_INSTRUCTION="Ви дружелюбний українськомовний чат-бот"

# Безпека та оптимізація
GEMINI_ENABLE_CACHE=true
GEMINI_RATE_LIMIT_RPM=60
```

Детальна документація: [`GEMINI_ENHANCED_INTEGRATION.md`](GEMINI_ENHANCED_INTEGRATION.md)

5. **Перевірте роботу (опціонально)**:
   ```bash
   python test_bot.py
   # Або нові інтеграційні тести
   python -m pytest test_integration_gemini.py -v
   ```

## 🐳 Docker Deployment

### Швидкий старт з Docker Compose

1. **Клонування та налаштування**:
   ```bash
   git clone https://github.com/your-username/pomiyka-bot.git
   cd pomiyka-bot
   
   # Копіюємо конфіг
   cp .env.example .env
   
   # Редагуємо токени
   nano .env  # або ваш улюблений редактор
   ```

2. **Запуск з docker-compose (рекомендовано)**:
   ```bash
   # Production запуск
   docker-compose -f docker-compose.prod.yml up -d
   
   # Або development версія
   docker-compose up -d
   
   # Перегляд логів в реальному часі
   docker-compose logs -f pomiyka-bot
   ```

3. **Моніторинг та управління**:
   ```bash
   # Статус контейнерів
   docker-compose ps
   
   # Перезапуск бота
   docker-compose restart pomiyka-bot
   
   # Зупинка
   docker-compose down
   
   # Повне очищення (видалить контейнери та образи)
   docker-compose down --rmi all -v
   ```

### Звичайний Docker (без compose)

```bash
# Збірка образу
docker build -t gryag-bot:latest .

# Запуск з монтуванням даних
docker run -d \
  --name gryag-bot \
  --restart unless-stopped \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/.env:/app/.env:ro \
  -e PYTHONUNBUFFERED=1 \
  gryag-bot:latest

# Логи
docker logs -f gryag-bot

# Під'єднання до контейнера
docker exec -it gryag-bot /bin/bash
```

### Docker Compose конфігурації

**docker-compose.yml** (development):
```yaml
version: '3.8'
services:
  pomiyka-bot:
    build: .
    container_name: gryag-bot-dev
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env:ro
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=DEBUG
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**docker-compose.prod.yml** (production):
```yaml
version: '3.8'
services:
  pomiyka-bot:
    image: gryag-bot:latest
    container_name: gryag-bot-prod
    restart: always
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./.env:/app/.env:ro
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
```

### Debugging в Docker

```bash
# Моніторинг ресурсів
docker stats gryag-bot

# Експорт логів
docker logs gryag-bot > bot-logs.txt 2>&1

# Backup БД з контейнера
docker exec gryag-bot python -c "from bot.modules.backup_manager import BackupManager; BackupManager().create_backup()"

# Копіювання backup з контейнера
docker cp gryag-bot:/app/backups ./local-backups
```

## ⚙️ Конфігурація (.env)

```env
TELEGRAM_BOT_TOKEN=your-bot-token
GEMINI_API_KEY=your-gemini-key
BOT_PERSONA_NAME=Гряг
BOT_PERSONA_DESC=Дружелюбний та кмітливий помічник з легким гумором!
BOT_CONTEXT_LIMIT=1000
BOT_MAX_CONTEXT_SIZE=10000
BOT_RANDOM_REPLY_CHANCE=0.5
BOT_SMART_REPLY_CHANCE=0.1
BOT_MIN_SILENCE_MINUTES=15
BOT_MAX_REPLIES_PER_HOUR=3
BOT_AUTONOMOUS_MODE=true
BOT_SPONTANEOUS_CHANCE=0.02
BOT_REACTION_CHANCE=0.05
BOT_REACTION_ON_MENTIONS=true
BOT_AUTO_SCAN_HISTORY=true
BOT_MAX_HISTORY_SCAN=500
BOT_DATA_DIR=data
ADMIN_ID=392817811

# Ігнорування старих повідомлень (проти спаму при перезапуску)
BOT_IGNORE_OLD_MESSAGES=true
BOT_MAX_MESSAGE_AGE_MINUTES=10

# Спонтанна активність
BOT_SPONTANEOUS_MIN_PAUSE=30
BOT_SPONTANEOUS_CHANCE=0.3

# Агресивний анти-спам
BOT_SPAM_THRESHOLD=5
BOT_SPAM_TIMEOUT=300
BOT_SPAM_REPLIES=тіха блять, хохли;не спамте;заткніться на хвилинку
```

## 🎮 Адмін-команди

- `/stats` — статистика бота (кількість повідомлень, чатів)
- `/help` — список команд  
- `/clear_context` — очистити весь контекст
- `/rescan` — повторне сканування історії чату (корисно якщо бот був доданий без доступу до історії)
- `/reactions` — показати доступні емоджі-реакції бота
- `/import_history <path.json> <chat_id>` — імпорт історії з Telegram Desktop

### Імпорт історії чату

Щоб імпортувати існуючу історію з Telegram Desktop:

1. В Telegram Desktop: Налаштування → Розширені → Експорт даних
2. Оберіть чат та експортуйте в JSON format  
3. Завантажте JSON файл на сервер
4. Використайте команду: `/import_history /path/to/chat.json -1001234567890`
   (замість `-1001234567890` підставте ID вашого чату)

**Примітка**: Імпорт великих файлів може зайняти час. Автоматичне сканування при додаванні в новий чат відбувається швидше.

### 🎭 Реакції бота

Гряг автоматично ставить емоджі-реакції на повідомлення:

**Коли бот реагує:**
- На згадки свого імені (@gryag_bot, гряг, грягік) — 70% шанс
- На питання (з ?, що, як, коли) — 30% шанс  
- На емоційні слова (класно, супер, вау) — 40% шанс
- На звичайні повідомлення — 5% шанс (налаштовується)

**Типи реакцій:**
- **Позитивні**: 👍❤️🔥🥰👏😁🎉🤩💯🏆 — на приємні повідомлення
- **Нейтральні/абсурдні**: 🤔🤯🙏👌🕊🤡🌚🌭⚡️🍌 — на звичайні
- **На питання**: 🤔🤯👌🙏 — показує роздуми

Використайте `/reactions` щоб побачити всі доступні реакції.

### 📊 Моніторинг Gemini API

Щоб відстежувати використання API:

1. **Google AI Studio**: [aistudio.google.com](https://aistudio.google.com)
2. **API Key Page**: переглядайте usage metrics
3. **Rate Limits**: у разі перевищення бот автоматично затримає відповіді

**Оптимізація використання:**
- Бот має вбудовану анти-спам систему 
- Контекст компресується автоматично
- Медіа-файли описуються абсурдними префіксами (не AI)
- **Ігнорування старих повідомлень**: бот не обробляє повідомлення старше 10 хвилин при перезапуску (проти спаму)
- **Rate limiting**: захист від flood control Telegram (3 повідомлення/хв на чат, 20/хв глобально)
- **Розумний error handling**: бот не створює каскадні помилки при збоях

## 📁 Структура проєкту

```
pomiyka-bot/
├── bot/
│   ├── main.py              # Головний файл бота
│   ├── bot_config.py        # Конфігурація персони та лімітів
│   └── modules/
│       ├── gemini.py        # Інтеграція з Gemini
│       ├── context.py       # Робота з контекстом (legacy)
│       ├── context_sqlite.py # SQLite для великої історії  
│       ├── chat_scanner.py  # Автосканування чатів
│       ├── smart_behavior.py # Анти-спам та автономність
│       ├── random_life.py   # Рандомні відповіді та "життя" 
│       ├── media_map.py     # Карта медіа-файлів
│       └── management.py    # Адмін-команди
├── data/                    # Персистентні дані (створюється автоматично)
│   ├── context.db          # SQLite база з контекстом
│   ├── media_map.json      # Карта медіа для економії токенів
│   └── chat_states.json    # Стан сканованих чатів
├── start.py                 # Скрипт запуску з перевіркою
├── Dockerfile              # Docker контейнер  
├── docker-compose.yml      # Зручний деплой
├── requirements.txt         # Залежності
├── .env.sample             # Приклад конфігурації
└── README.md               # Цей файл
```

## 🎯 Що робить бот автоматично

### При першому запуску в чаті:
1. **Автоматична ініціалізація**: сканує та позначає чат як готовий до роботи
2. **Створення бази**: автоматично створює SQLite базу для контексту
3. **Початковий контекст**: починає збирати історію з перших повідомлень

### В роботі:
- **Збереження контексту**: кожне повідомлення автоматично зберігається в базу
- **Анти-спам**: автоматично відстежує частоту відповідей та витримує паузи
- **Настрій чату**: аналізує атмосферу та підлаштовується
- **Спонтанна активність**: іноді пише сам, але не спамить

## 🎯 TODO
- [ ] Підтримка груп/топіків  
- [ ] Веб-інтерфейс для адміністрування
- [ ] Експорт контексту
- [ ] ~~Docker-контейнер~~ ✅ Готово
- [ ] Метрики та аналітика
- [ ] Health check для Docker

## 🐛 Відомі проблеми
- Lint-помилки в коді (це нормально для швидкого прототипу)
- Gemini API може бути нестабільним
- Великий контекст може повільно завантажуватися

---
*Створено з ❤️ та абсурдом для українських чатів*
