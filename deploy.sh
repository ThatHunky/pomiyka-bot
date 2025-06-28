#!/bin/bash
# Скрипт швидкого деплою Гряг-бота з покращеннями

set -e  # Зупинити при помилці

echo "🚀 Починаємо деплой Гряг-бота..."
echo "=================================="

# Функція логування
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Перевіряємо наявність Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не встановлено"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не встановлено"
    exit 1
fi

log "✅ Docker та Docker Compose доступні"

# Перевіряємо .env файл
if [ ! -f ".env" ]; then
    log "❌ Файл .env не знайдено"
    if [ -f ".env.sample" ]; then
        log "📄 Копіюємо .env.sample в .env"
        cp .env.sample .env
        log "⚠️ Відредагуйте .env файл та запустіть скрипт знову"
        exit 1
    else
        log "❌ .env.sample також не знайдено"
        exit 1
    fi
fi

log "✅ Файл .env знайдено"

# Створюємо backup
log "📦 Створюємо backup..."
if [ -d "data" ]; then
    backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    cp -r data "$backup_dir/"
    log "✅ Backup створено: $backup_dir"
else
    log "ℹ️ Директорія data не існує, пропускаємо backup"
fi

# Зупиняємо попередню версію
log "⏹️ Зупиняємо попередню версію..."
docker-compose down --remove-orphans || true

# Збираємо новий образ
log "🏗️ Збираємо новий образ..."
docker-compose build --no-cache

# Запускаємо сервіси
log "▶️ Запускаємо сервіси..."
docker-compose up -d

# Чекаємо запуску
log "⏳ Чекаємо запуску бота..."
sleep 15

# Перевіряємо health
log "🏥 Перевіряємо health check..."
for i in {1..10}; do
    if curl -f http://localhost:8080/health &>/dev/null; then
        log "✅ Bot успішно запущено!"
        break
    else
        if [ $i -eq 10 ]; then
            log "❌ Health check не пройшов після 10 спроб"
            log "📋 Логи контейнера:"
            docker-compose logs --tail=20 gryag-bot
            exit 1
        fi
        log "⏳ Спроба $i/10..."
        sleep 3
    fi
done

# Показуємо статус
log "📊 Статус сервісів:"
docker-compose ps

# Очищаємо старі образи
log "🧹 Очищаємо старі образи..."
docker image prune -f

# Показуємо корисну інформацію
echo ""
echo "🎉 Деплой завершено успішно!"
echo "=================================="
echo "🌐 Веб-дашборд: http://localhost:8080"
echo "📊 Health check: http://localhost:8080/health"
echo "📈 Метрики: http://localhost:8080/metrics"
echo ""
echo "📋 Корисні команди:"
echo "  Логи бота:     docker-compose logs -f gryag-bot"
echo "  Статус:        docker-compose ps"
echo "  Зупинити:      docker-compose down"
echo "  Перезапустити: docker-compose restart gryag-bot"
echo ""

# Показуємо останні логи
log "📋 Останні логи бота:"
docker-compose logs --tail=10 gryag-bot

echo "🚀 Готово! Бот працює."
