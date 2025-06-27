# ФИНАЛЬНАЯ ВЕРСИЯ: Полный парсер YClients с Playwright
FROM python:3.10-slim
WORKDIR /app

# Системные зависимости для Playwright
RUN apt-get update && apt-get install -y \
    wget curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir fastapi uvicorn asyncpg playwright

# Устанавливаем браузеры Playwright
RUN playwright install chromium --with-deps

# Копируем финальное приложение
COPY final_parser.py .

EXPOSE 8000
CMD ["python", "final_parser.py"]
