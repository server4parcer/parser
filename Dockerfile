# PLAYWRIGHT VERSION: Full browser automation for 16GB TimeWeb
FROM python:3.10-slim
WORKDIR /app

# Environment for Playwright
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers

# Install system dependencies for Playwright
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

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers for TimeWeb
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy application code
COPY . .

# Create directories (no volumes for TimeWeb)
RUN mkdir -p /app/data /app/logs

# TimeWeb required port
EXPOSE 8000

# Health check for TimeWeb
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Playwright YClients parser startup
CMD ["python", "playwright_parser_startup.py"]
