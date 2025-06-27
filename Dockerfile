# ИСПРАВЛЕННАЯ ВЕРСИЯ: Гарантированная установка Playwright
FROM python:3.10-slim
WORKDIR /app

# Установка системных зависимостей для Playwright
RUN apt-get update && apt-get install -y \
    wget curl ca-certificates \
    libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2 \
    libatspi2.0-0 libgtk-3-0 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
RUN pip install --no-cache-dir fastapi uvicorn asyncpg playwright

# Установка браузеров Playwright (принудительно)
RUN playwright install chromium
RUN playwright install-deps chromium

# Проверка установки браузеров
RUN playwright --version
RUN ls -la /root/.cache/ms-playwright/ || echo "No playwright cache found"

# Копирование приложения
COPY final_parser.py .

EXPOSE 8000
CMD ["python", "final_parser.py"]
