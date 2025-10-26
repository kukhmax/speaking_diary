# Dockerfile для Backend
# Python 3.13 - последняя стабильная версия (октябрь 2024)
FROM python:3.13-slim

# Установка рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование файла зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всех файлов приложения
COPY . .

# Создание директории для базы данных
RUN mkdir -p /app/data

# Открытие порта
EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')"

# Запуск приложения
CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "4"]