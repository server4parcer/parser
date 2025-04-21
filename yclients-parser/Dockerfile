# Используем официальный образ Python как базовый
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers

# Устанавливаем необходимые пакеты системы
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    git \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей в контейнер
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем Playwright и нужные браузеры
RUN playwright install chromium \
    && playwright install-deps chromium

# Копируем все файлы проекта в контейнер
COPY . .

# Создаем необходимые директории
RUN mkdir -p /app/data/export \
    && mkdir -p /app/logs

# Проверяем структуру проекта
RUN ls -la /app

# Устанавливаем права на выполнение скриптов
RUN chmod +x /app/scripts/*.sh

# Открываем порт для API
EXPOSE 8000

# Устанавливаем точку входа
ENTRYPOINT ["python", "src/main.py"]

# Аргументы по умолчанию для запуска всех компонентов
CMD ["--mode", "all"]
