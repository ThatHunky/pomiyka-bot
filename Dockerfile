# Dockerfile для Гряг-бота
FROM python:3.12-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли залежностей
COPY requirements.txt .

# Встановлюємо залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо код проєкту
COPY . .

# Створюємо директорії для персистентних даних
RUN mkdir -p /app/data

# Встановлюємо змінну середовища для персистентних даних
ENV BOT_DATA_DIR=/app/data

# Відкриваємо порт (якщо потрібно для webhook)
EXPOSE 8000

# Запускаємо бота
CMD ["python", "start.py"]
