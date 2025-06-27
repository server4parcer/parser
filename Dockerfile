# ФИНАЛЬНАЯ ВЕРСИЯ: Полный парсер YClients с Playwright
FROM python:3.10-slim
WORKDIR /app

# Системные зависимости для Playwright
RUN apt-get update && apt-get install -y \
    wget curl ca-certificates \
    libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libxss1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir fastapi uvicorn asyncpg playwright

# Устанавливаем браузеры Playwright (исправленная версия)
RUN playwright install --with-deps chromium

# Копируем финальное приложение
COPY final_parser.py .

EXPOSE 8000
CMD ["python", "final_parser.py"]
