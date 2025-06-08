# Dockerfile для TimeWeb Cloud Apps
# Оптимизирован для работы БЕЗ volumes и с внешней БД

FROM python:3.10-slim

# Метаданные
LABEL maintainer="YCLIENTS Parser Team"
LABEL version="1.0-timeweb"
LABEL description="YCLIENTS Parser for TimeWeb Cloud Apps"

# Рабочая директория
WORKDIR /app

# Переменные окружения для оптимизации
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    git \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
# Копирование requirements.txt для кэширования слоев
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Установка Playwright и браузеров
RUN playwright install chromium && \
    playwright install-deps chromium

# Копирование всего исходного кода
COPY . .

# Создание директорий ВНУТРИ контейнера (БЕЗ volumes)
# Данные будут храниться в памяти/внешней БД
RUN mkdir -p /app/data/export && \
    mkdir -p /app/logs && \
    chmod +x /app/scripts/*.sh 2>/dev/null || true

# Создание пользователя для безопасности
RUN groupadd -r yclients && useradd -r -g yclients yclients && \
    chown -R yclients:yclients /app
USER yclients

# Порт приложения
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/status || exit 1

# Точка входа
ENTRYPOINT ["python", "src/main.py"]

# Команда по умолчанию
CMD ["--mode", "all"]
