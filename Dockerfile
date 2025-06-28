# Покращений Dockerfile для Гряг-бота з оптимізаціями
FROM python:3.12-slim as builder

# Встановлюємо системні залежності для збірки
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Створюємо користувача для безпеки
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли залежностей
COPY requirements.txt requirements-dev.txt* ./

# Встановлюємо залежності з кешуванням
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Встановлюємо runtime залежності
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Створюємо користувача
RUN groupadd -r botuser && useradd -r -g botuser botuser

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо залежності з builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Завантажуємо українську мовну модель для spaCy (якщо потрібно)
RUN python -m spacy download uk_core_news_sm || echo "spaCy model download skipped"

# Копіюємо код проєкту
COPY . .

# Створюємо директорії для персистентних даних
RUN mkdir -p /app/data && \
    mkdir -p /app/logs && \
    chown -R botuser:botuser /app

# Встановлюємо змінні середовища для продуктивності
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    USE_ASYNC_DB=true \
    GEMINI_ENABLE_CACHE=true \
    BOT_DATA_DIR=/app/data

# Змінюємо власника файлів
USER botuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || python -c "import sys; sys.exit(1)"

# Expose порт для моніторингу (опціонально)
EXPOSE 8080

# Команда запуску
CMD ["python", "start.py"]
ENV PYTHONUNBUFFERED=1

# Створюємо non-root користувача для безпеки
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Health check endpoint (опціонально)
EXPOSE 8000

# Запускаємо бота
CMD ["python", "start.py"]
