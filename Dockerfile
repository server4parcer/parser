FROM python:3.10-slim

# Установка рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка Playwright с браузерами
RUN playwright install chromium --with-deps

# Копирование всего кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p /app/data /app/logs

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["python", "src/main.py", "--mode", "all"]
