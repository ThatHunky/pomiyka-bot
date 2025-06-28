# Dockerfile для Гряг-бота
FROM python:3.12-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли залежностей
COPY requirements.txt .

# Встановлюємо залежності
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Завантажуємо українську мовну модель для spaCy (якщо потрібно)
RUN python -m spacy download uk_core_news_sm || echo "spaCy model download skipped"

# Копіюємо код проєкту
COPY . .

# Створюємо директорії для персистентних даних
RUN mkdir -p /app/data

# Встановлюємо змінні середовища
ENV BOT_DATA_DIR=/app/data
ENV PYTHONUNBUFFERED=1

# Створюємо non-root користувача для безпеки
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Health check endpoint (опціонально)
EXPOSE 8000

# Запускаємо бота
CMD ["python", "start.py"]
