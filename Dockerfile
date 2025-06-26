# Dockerfile для TimeWeb Cloud Apps - ИСПРАВЛЕННАЯ ВЕРСИЯ
FROM python:3.10-slim

# Рабочая директория
WORKDIR /app

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Установка Playwright браузеров
RUN playwright install chromium && \
    playwright install-deps chromium

# Копирование исходного кода
COPY . .

# Создание директорий
RUN mkdir -p /app/data/export /app/logs

# Права доступа
RUN chmod -R 755 /app

# Порт приложения
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/status || exit 1

# Максимально простая точка входа
ENTRYPOINT ["python", "super_simple_startup.py"]
