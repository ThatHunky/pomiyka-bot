# 🚀 Інструкція з деплою Гряг-бота

## 📋 Швидкий старт для продакшн

### 1. 📁 Розпакування архіву
```bash
# Завантажте архів на сервер
unzip gryag-bot-v2.8-docker-optimized-*.zip
cd gryag-bot-*/
```

### 2. ⚙️ Налаштування конфігурації
```bash
# Створіть файл з вашими налаштуваннями
cp .env.sample .env
nano .env
```

**Обов'язково заповніть:**
- `TELEGRAM_BOT_TOKEN` - токен від @BotFather
- `GEMINI_API_KEY` - API ключ з Google AI Studio
- `ADMIN_ID` - ваш Telegram ID

### 3. 🐳 Запуск через Docker

#### Для розробки:
```bash
docker-compose up -d
```

#### Для продакшн:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. 📊 Моніторинг

```bash
# Перевірка статусу
docker-compose ps

# Перегляд логів
docker-compose logs -f gryag-bot

# Health check
docker exec gryag-bot python -c "from bot.modules.health_checker import HealthChecker; hc = HealthChecker(); print(hc.get_health_status())"
```

### 5. 🔧 Управління

```bash
# Зупинка
docker-compose down

# Перезапуск
docker-compose restart

# Оновлення (з новим архівом)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📁 Структура проекту в архіві

```
gryag-bot-v2.8-docker-optimized/
├── 📄 requirements.txt          # Python залежності
├── 🐍 start.py                  # Скрипт запуску
├── 🐳 Dockerfile                # Docker образ
├── 🐳 docker-compose.yml        # Docker Compose (dev)
├── 🐳 docker-compose.prod.yml   # Docker Compose (prod)
├── 📄 .dockerignore             # Виключення для Docker
├── 📄 .env.sample               # Приклад конфігурації
├── 📖 README.md                 # Документація
├── 📋 CHANGELOG.md              # Історія змін
├── 🧪 test_*.py                 # Критичні тести
└── 🤖 bot/                      # Код бота
    ├── main.py                  # Головний файл
    ├── bot_config.py            # Конфігурація
    └── modules/                 # Модулі бота
        ├── gemini_enhanced.py   # Gemini API інтеграція
        ├── enhanced_behavior.py # Розумна поведінка
        ├── rate_limiter.py      # Обмеження швидкості
        ├── backup_manager.py    # Бекапи
        ├── health_checker.py    # Моніторинг здоров'я
        └── ... (інші модулі)
```

## 🔒 Безпека

- ✅ Non-root користувач в Docker контейнері
- ✅ Read-only mount для .env файлу
- ✅ Обмеження ресурсів CPU/RAM
- ✅ Health checks для моніторингу
- ✅ Автоматичні бекапи бази даних

## 🔧 Особливості версії v2.8

- ✅ Оптимізований Docker образ
- ✅ Покращені health checks
- ✅ Автоматичне завантаження української мовної моделі spaCy
- ✅ Продакшн-готова конфігурація
- ✅ Логування з ротацією
- ✅ Обмеження ресурсів

## 📞 Підтримка

При виникненні проблем:
1. Перевірте логи: `docker-compose logs gryag-bot`
2. Перевірте health status
3. Переконайтеся, що .env файл правильно налаштований
4. Перевірте, що Docker має достатньо ресурсів

## 🔄 Оновлення

Для оновлення до нової версії:
1. Зробіть бекап даних: `docker exec gryag-bot python -c "from bot.modules.backup_manager import backup_database; backup_database()"`
2. Завантажте новий архів
3. Зупиніть поточну версію: `docker-compose down`
4. Розгорніть нову версію за цією інструкцією
