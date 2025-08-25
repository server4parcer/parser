# PLAYWRIGHT VERSION: With browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories (no volumes)
RUN mkdir -p /app/data /app/logs

# TimeWeb required port
EXPOSE 8000

# Health check for TimeWeb
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Playwright YClients parser with real JavaScript support
CMD ["python", "playwright_parser_startup.py"]
