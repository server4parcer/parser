# ФИНАЛЬНАЯ ВЕРСИЯ: Полный парсер YClients с Playwright
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
WORKDIR /app

# Устанавливаем дополнительные Python зависимости
RUN pip install --no-cache-dir fastapi uvicorn asyncpg

# Копируем финальное приложение
COPY final_parser.py .

EXPOSE 8000
CMD ["python", "final_parser.py"]
